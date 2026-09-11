---
type: Concept
title: MindSpeed-MM 数据流水（在线重排 + 异步预处理 + 序列 Packing）
description: MindSpeed-MM 多模态训练数据流水：数据组装（多数据集 repeat_time 混采、_init_return_dict/_filter_return_dict_keys 字段裁剪）+ 三段互补技术。在线数据重排（--use-data-balance，GBSImageDataBalance）以 Σsub_seq² 为算力度量、贪心装桶（post_global_balancing_greedy_without_pad，最长播种 + 投向平方和最小桶）按 max_seq_len packing 后用 all_gather+all_to_all 在 DP 间双向重排，配 EncoderBalanceComm（--encoder-dp-balance，按 patch 数 alltoall）让编码器与 LLM 两段各自均衡，MBSImageDataBalance 负责编码器后还原。异步预处理 iterable dataset（async_preprocess，限 streaming+base 模式）：先 DistributedIterableDataset 分片再异步，单 producer 顺序读派 sequence_idx、多 worker 并发 _preprocess_item、主迭代器靠 pending_results+next_sequence_idx 按序重排输出，掩盖预处理/IO 时延；buffer_size/num_workers 归一化与吞吐-内存调参。序列 Packing（use_txt_dynamic_batching，DynamicBatchingDataLoader+TextBatchingStrategy/DynBszBuffer）：按 attention_mask 去 pad、贪心选样拼到近 max_seq_len 成 TND layout [1,ΣT]+seqlens，降 pad 并均衡卡间 token。关键术语：online rearrange、all-to-all、Σseq²、TND layout、seqlens、sequence_idx、buffer。
tags:
- task.optimization
- topic.multimodal
- topic.data_pipeline
- topic.data_movement.layout_transform
status: stable
sources:
- resource: https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/README.md
  role: primary
- resource: https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/online_data_rearrange.md
  role: supporting
created_at: '2026-06-29T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MindSpeed-MM 数据流水（在线重排 + 异步预处理 + 序列 Packing）

## Summary

多模态训练样本是文本 / 图像 / 视频 / 音频 token 交叉排成的序列，长度随动态分辨率剧烈起伏：图大文长的样本编码器与骨干网络算得久，图小文短的算得快，DP 各卡前向耗时拉开，到梯度 all-reduce 处「快卡等慢卡」。同时单条样本的预处理（模板拼接、tokenize、模态输入整理）很重，串在训练主线程里直接拖吞吐；而批内按最大长度 pad 又把短样本的算力与显存浪费掉。MindSpeed-MM 的数据侧用三段互补流水应对：**在线数据重排**（`--use-data-balance`）按样本长度在 DP 间重排、让编码器与 LLM 两段算力各自均衡；**异步预处理 iterable dataset**（`async_preprocess`）把单样本预处理甩给后台 worker、用流水掩盖预处理 / IO 时延；**序列 Packing**（`use_txt_dynamic_batching`）把多条变长序列拼到近 `max_seq_len` 再以 TND layout 喂入，降 pad 并均衡卡间 token 数。三者落在 `mindspeed_mm/data/` 与 `mindspeed_mm/utils/data_balance/`，是 [mindspeed-mm](../frameworks/mindspeed_mm.md) 理解类多模态训练（Qwen2/2.5/3-VL、Qwen-Omni、InternVL）的数据入口。

## 数据组装：多数据集混采与返回字典裁剪

重排前的第一步是把多份数据组装成统一样本流。理解模型支持多数据集训练：`basic_parameters` 由单对象改为对象列表，每项给 `data_path`（标注 json）、`data_folder`（图像 / 视频根目录）与 `repeat_time`（该集的重复采样倍率，用来调混采配比），InternVL 已支持这种写法。逐样本的取数与字段在 `multimodal_dataset.py` 的 `get_item` 里成形：`_init_return_dict` 先建出标准返回字典（`pixel_values`/`image_flags`/`input_ids`/`labels`/`attention_mask` 等），`return` 前 `_filter_return_dict_keys` 过滤掉多余 key——新模型要带回额外字段，得先在 `_init_return_dict` 里登记。图像 / 视频预处理逻辑挂在 `multimodal_image_video_preprocess.py`、模型专属 `preprocess` 挂在 `data_utils/utils.py`。组装产出的逐样本字典正是后续重排 / Packing / 异步预处理三段共同的输入单元。

## 在线数据重排：编码器均衡换 LLM 均衡的双向 all-to-all

负载不均衡分两层：`intra-microbatch`（DP 间，各卡 global batch 的样本总算力不等）与 `inter-microbatch`（DP 内，同一卡各 microbatch 之间不等）。在线重排针对 DP 间这层，目标是让 **LLM 的 DP 算力均衡**——以「各子序列长度的平方和」`Σ sub_seq²` 作为算力度量（注意力是 O(S²)），约束是先按 `max_seq_len` 把序列 packing 拼接。整条流水按这六步走：数据按条件 / 目标组装 → dataloader 读出后按编码器 DP 负载重排数据索引 → 用 all-to-all 按索引把数据搬到对应卡 → 编码器在均衡后的负载上算 → 再按**原始索引**做一次 all-to-all、把 embed 还原成 LLM 负载均衡的布局 → LLM 在均衡后的负载上算。一次重排服务编码器、一次还原服务 LLM，两段各取所需。

`--use-data-balance` 由 `GBSImageDataBalance` 承接（当前仅支持 ViT 负载均衡）。`build_balanced_train_data_iterator` 取一个 global batch 后：先把图像按 `image_grid_thw` 拆成逐张样本、文本（`input_ids/attention_mask/labels`）逐条拆开并算各自长度；`_data_balance` 用 `all_gather` 收齐全 DP 的长度，交给排序算法生成「样本 → 目标卡」的 `rank_table`，据此 `all_to_all` 把数据重新分发；`get_global_balanced_data` 再把文本按本批最长有效长度统一 pad、按 `balance_data_mapping_index` 把样本换回位置、切成 microbatch。排序算法 `post_global_balancing_greedy_without_pad` 是带容量上限的贪心装桶：序列按长度降序，先用最长的 `num_groups` 条各占一桶，余下逐条投到**当前平方和最小**的桶（`dp_group_total_length[:, 1].argmin()`，桶值累加 `length²`），桶满 `max_batch_capacity` 即从候选剔除——于是各卡的 `Σ seq²`（即 LLM 注意力算力）趋于一致，且全程不引入 padding。

编码器那段的均衡由独立的 `EncoderBalanceComm`（`--encoder-dp-balance`，beta，当前限 InternVL）完成：前向前统计各 DP rank 的 patch 数，用 all-to-all 把多 patch 卡的部分 ViT/MLP 计算挪给少 patch 卡，算完再 all-to-all 把结果送回原 rank——度量是 patch 数而非 `seq²`，与 LLM 侧度量不同，所以才需要「编码器布局 ↔ LLM 布局」两次搬运。DP 内（`inter-microbatch`）那层另有 `MBSImageDataBalance`（`--use-image-mbs-data-balance`），它带 `need_rev=True`，`reverse_img_balance_data`（落到 `_recover_image_data`）在编码器算完后把 `hidden_state` 经 `all_to_all` + 原始索引（`pixel_values_data_list`）还原回原始 DP 顺序，供后续按 LLM 布局消费。重排只在 `image_encoder_dp > 1` 时有意义，DP=1 会告警并退化为纯开销。

```mermaid
flowchart LR
  RAW["global batch<br/>逐样本拆 + 算长度"] --> RE["all_gather 长度<br/>贪心装桶(min Σseq²)<br/>→ rank_table"]
  RE --> A2A1["all_to_all 重排<br/>→ 编码器负载均衡"]
  A2A1 --> ENC["ViT / MLP 编码<br/>(patch 数均衡)"]
  ENC --> A2A2["all_to_all 还原<br/>(按原始索引)<br/>→ embed 随 LLM 均衡"]
  A2A2 --> LLM["LLM 前向<br/>(Σseq² 均衡)"]
```

## 异步预处理 iterable dataset：单 producer + 多 worker + 按序重排

流式（HuggingFace `streaming=True` 的 `IterableDataset`）训练边读边处理，单样本预处理又重，全塞主线程会直接拉低吞吐。`AsyncPreprocessIterableDataset` 把单条样本的预处理从训练主线程解耦给多个后台 worker 并发执行，同时保持样本的逻辑顺序不变、不改 `preprocess_fn` 签名。它的设计不是让多 worker 抢着遍历同一个上游流（那会重复读取、顺序错乱、各 rank 偏移不一致），而是「单线程顺序读上游 + 多 worker 并发预处理 + 按序重排输出」。

关键是**先分片、再异步**：`DistributedIterableDataset` 先按 `idx % num_dp == dp_rank` 把原始样本流切到各 DP 副本，`AsyncPreprocessIterableDataset` 只对本 rank 的子流做异步预处理。反过来先异步再分片，每个 rank 都要先处理整份上游流再丢弃大部分，既重复预处理又有额外队列开销；且若预处理阶段发生样本过滤或一对多展开，后置分片面对的是输出流、边界会漂移，破坏副本间对齐。

`__iter__` 内起三类角色，跑在 `task_queue`（容量 = `num_workers`）/ `result_queue`（容量 = `buffer_size`）/ `stop_event` 上：

- **producer 线程**：`enumerate(self.dataset)` 顺序遍历本 rank 子流，给每条样本派一个单调递增的 `sequence_idx`（重排的唯一依据），把 `(sequence_idx, item)` 投进 `task_queue`；遍历完投 `num_workers` 个 `task_done` 哨兵。上游始终只有这一个读取入口，从根上杜绝并发读乱序。
- **worker 线程（`num_workers` 个）**：从 `task_queue` 取任务，`_preprocess_item` 把单样本临时包成长度为 1 的 batch 调 `preprocess_fn`、再拆回单样本列表（兼容一条样本展开成多条），把 `("result", sequence_idx, processed_items)` 投进 `result_queue`；取到哨兵则投 `("done", …)` 退出。
- **主迭代器**：维护 `pending_results` 缓存与 `next_sequence_idx` 游标，只有当 `next_sequence_idx` 已在 `pending_results` 时才 `yield`——快 worker 的结果至多「先到先缓存」、不能「先到先输出」；同一原始样本展开的 `processed_items` 作为整体连续吐出，不与别条交叉。worker 完成时序会乱，输出顺序不会乱。

配置归一化在 `_resolve_async_config`：二者都未配 → `buffer_size=8`、`num_workers=min(8, cpu_count)`；只配 `buffer_size` → `num_workers` 取不超 CPU 的合理值；只配 `num_workers` → `buffer_size` 回落同值；都配且 `buffer_size < num_workers` 则告警可能队列阻塞。实际接入时 `num_workers` 取 `preprocessing_num_workers`、`buffer_size` 取 `async_preprocess_buffer_size`。`async_preprocess` 仅在 `streaming: true` 生效，且依赖 `base` 加载模式（`sampler` 模式要 `len(dataset)`，与 `IterableDataset` 不兼容，流式下也不支持全局 shuffle）。异常（producer 读失败或 worker 预处理失败）写 `error` 消息触发 `stop_event`，主线程把异常抛回训练侧，`finally` 统一 `join` 后台线程避免悬挂。Megatron 路径在 `qwen2vl_dataset.py`、FSDP2 路径在 `fsdp/data/datasets/huggingface/qwen2vl_dataset.py`，两条链路顺序一致。

`buffer_size` 是吞吐与内存的旋钮：过小则任务 / 结果队列易被取空或堆满，worker 饥饿、主线程直接等数据，吞吐下降；过大则缓存更多在途样本及其预处理结果，图像 / 视频 / 音频大样本下 CPU 内存压力明显。调参可按「单样本预处理耗时 ÷ 训练侧单样本消费耗时」之比来定：预处理明显慢则先加 `preprocessing_num_workers`、再把 `buffer_size` 设到不小于 worker 数；两者接近则 `buffer_size` 取 `num_workers`~`2·num_workers` 吸收波动；训练更慢则 `buffer_size` 维持在 `num_workers` 附近即可。

## 序列 Packing：TND 拼接降 pad、均衡卡间 token

图像 token 数与文本长度的双重异构让批内序列长度差异巨大，按批内最大长度 pad 浪费显存，且不顾 DP 组间 token 关系还会引入卡间不均。序列 Packing 把多条序列拼到近似 `max_seq_len` 作为一个批次、模型以 **TND layout**（拼接后整段 `[1, ΣT]` + 逐样本真实长度 `seqlens`）处理；为有足够样本可选，用 `buffer` 暂存数据，拼接时从 buffer 弹出能凑到近 `max_seq_len` 的一组。这样每卡 token 总数一致，省 padding 显存的同时均衡卡间负载。开关 `use_txt_dynamic_batching`（默认 `false`），`max_seq_len`（拼接目标长度，默认 2048）、`dynamic_batch_buffer_size`（buffer 大小，默认 200），当前支持 Qwen3-VL。

`DynamicBatchingDataLoader` 是实现：`_get_data_from_dataloader` 从原 dataloader 取一批、沿 batch 维拆成逐条样本，并按 `attention_mask.bool()` **剥掉每条的 padding**（`input_ids/labels/attention_mask` 只留有效位）、按 `image_grid_thw` 拆 `pixel_values`；非可打包数据（长度与 mbs 不符的）移到 `non_packing_data` 旁路。样本进 `TextBatchingStrategy` 的 `DynBszBuffer`，`is_full_filled` 要求 buffer 样本数 ≥ `buffer_size` **且**累计 token 数 ≥ `max_seq_len` 才出一个 microbatch。`get_samples` 贪心选样本：累计真实长度（`attention_mask.sum()`）逼近 `max_seq_len` 即止，首条样本即便超长也强制纳入（`force`），避免空批。`collect_fn` 把选中样本的 `input_ids/labels/attention_mask` 拼接后 `unsqueeze(0)` 成 `[1, ΣT]`、`pixel_values` 在 TND 下直接 `cat`，并产出 `seqlens`（逐样本真实长度）与 `indices`——`seqlens` 正是 TND 变长注意力切分各子序列的依据，与通用变长打包同一套 layout 契约（见 [data-packing-varlen](data_packing_varlen.md)）。相比按批最大长度 pad，每个打包批是近 `max_seq_len` 的真实 token、几乎无填充，且各卡 token 数对齐，DP 负载随之均衡。

## 三段流水的协同与取舍

| 段 | 开关 | 解决的问题 | 关键机制 |
|---|---|---|---|
| 在线数据重排 | `--use-data-balance`（+`--encoder-dp-balance`） | DP 间编码器 / LLM 算力不均 | 贪心装桶按 `Σseq²` 均衡 LLM、按 patch 数均衡编码器，双向 all-to-all |
| 异步预处理 | `async_preprocess`（限 `streaming` + `base`） | 主线程等预处理 / IO | 单 producer 顺序读 + 多 worker 并发 + `sequence_idx` 按序重排 |
| 序列 Packing | `use_txt_dynamic_batching` | 批内 pad 浪费 + 卡间 token 不均 | buffer 选样拼到近 `max_seq_len`、TND layout + `seqlens` |

三者作用层级不同、可叠加：重排管 DP 间均衡、Packing 管批内拼接与卡间 token 对齐、异步预处理管流式吞吐，共同把多模态变长、异构、重预处理的数据喂成均衡且不空转的训练输入。在 `hetero_parallel` 下编码器 DP 与 LLM DP 取值不同（见 [hetero-parallel](../parallelism/hetero_parallel.md)），在线重排的「编码器布局 ↔ LLM 布局」两次搬运正服务这种分组并行。

## Evidence

- [mindspeed-mm](https://gitcode.com/Ascend/MindSpeed-MM) — [`docs/zh/features/online_data_rearrange.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/online_data_rearrange.md)（intra/inter-microbatch 两层不均、`Σsub_seq²` 度量、六步重排流程、`--use-data-balance` 限 ViT）、[`docs/zh/features/encoder_dp_balance.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/encoder_dp_balance.md)（patch 数不均、alltoall 重分配、`--encoder-dp-balance` beta 限 InternVL）
- [mindspeed-mm](https://gitcode.com/Ascend/MindSpeed-MM) — [`docs/zh/features/async_preprocess_iterable_dataset.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/async_preprocess_iterable_dataset.md)（先分片再异步、producer/worker/按序重排、`async_preprocess`/`async_preprocess_buffer_size` 语义、base vs sampler、调参建议）、[`docs/zh/features/seqpack.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/seqpack.md)（拼接近 max_seq_len、TND layout、`use_txt_dynamic_batching`/`max_seq_len`/`dynamic_batch_buffer_size` 默认值、限 Qwen3-VL）、[`docs/zh/features/multimodal_dataset.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/multimodal_dataset.md)（多数据集 `basic_parameters` 列表、`_init_return_dict`/`_filter_return_dict_keys` 数据模块接入）
- [`mindspeed_mm/utils/data_balance/data_balance.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/utils/data_balance/data_balance.py) — `GBSImageDataBalance.build_balanced_train_data_iterator`（拆样本 / `EncoderBalanceComm` 前置 / `get_global_balanced_data` 统一 pad + `balance_data_mapping_index` 换位）、`_data_balance`（`all_gather` 长度 + `all_to_all` 重排）、`MBSImageDataBalance.reverse_img_balance_data`/`_recover_image_data`（编码器后按原序还原 `hidden_state`）
- [`mindspeed_mm/utils/data_balance/balance_sorting_algo.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/utils/data_balance/balance_sorting_algo.py) — `post_global_balancing_greedy_without_pad`（降序 + 最长 `num_groups` 播种 + 投向 `Σlength²` 最小桶 + 满 `max_batch_capacity` 剔除）、`post_mbs_balancing_greedy_without_pad`
- [`mindspeed_mm/data/datasets/qwen2vl_dataset.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/data/datasets/qwen2vl_dataset.py) — `AsyncPreprocessIterableDataset`（`_resolve_async_config` 归一化、`_preprocess_item` 单样本批量化、`__iter__` 的 producer/worker/`pending_results`+`next_sequence_idx` 按序重排、`stop_event` 异常传播）、`get_qwen2vl_dataset`（`DistributedIterableDataset` 先分片再包异步）
- [`mindspeed_mm/data/dataloader/dynamic_batching_dataloader.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/data/dataloader/dynamic_batching_dataloader.py)、[`mindspeed_mm/data/dataloader/batching_strategy.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/data/dataloader/batching_strategy.py) — `DynamicBatchingDataLoader`（按 `attention_mask` 去 pad、`collect_fn` 拼 `[1,ΣT]` + `seqlens`/`indices`）、`TextBatchingStrategy`/`DynBszBuffer`（`is_full_filled` 双条件、`get_samples` 贪心逼近 `max_seq_len` + `force` 首样本）
- [`mindspeed_mm/arguments.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/arguments.py) — `--use-data-balance`/`--encoder-dp-balance`/`--use-image-mbs-data-balance`/`--use-txt-dynamic-batching`/`--max-seq-len`/`--dynamic-batch-buffer-size` 参数定义
- [`mindspeed_mm/training.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/training.py) — `use_data_balance` 初始化 `GBSImageDataBalance` + 每步 `build_balanced_train_data_iterator`、`use_txt_dynamic_batching` 路径下跨 DP `all_gather` 已消费样本数统计 batch

## Links

- [data-packing-varlen](data_packing_varlen.md)（通用变长 / EOD 序列打包与 TND layout；本页序列 Packing 是多模态在线变体，共用 `seqlens` 驱动的 TND 契约）
- [hetero-parallel](../parallelism/hetero_parallel.md)（MM 分组并行 + 动态 DP-CP；编码器 DP 与 LLM DP 取值不同，在线重排的双向搬运服务这种异构并行）
- [mindspeed-mm](../frameworks/mindspeed_mm.md)（三段数据流水所在框架；理解类多模态训练的数据入口）