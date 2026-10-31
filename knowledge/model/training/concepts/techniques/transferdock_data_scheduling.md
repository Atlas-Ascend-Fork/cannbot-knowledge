---
type: Concept
title: TransferDock（RL 数据面：训推各 worker 间样本调度交换）
description: TransferDock 是 MindSpeed-RL 在 rollout、reward、advantage、reference 与 actor worker 之间交换样本的数据面。GRPOTransferDock 以列存保存 prompts、responses、rewards、log-prob 和 advantages，用数据就绪矩阵与各 consumer 独立消费位图驱动异步取放；不足一批时等待，满足条件后可随机或按序列长度均衡采样。DAPO 通过双 dock 过滤零方差组，partial-rollout 复用同一状态结构处理续推与逐出。
tags:
- task.optimization
- topic.reinforcement_learning
- topic.model_serving
- topic.data_pipeline
status: stable
sources:
- resource: cann-recipes-raw/mindspeed-rl/adb494ad777ef4314bca717b56983feb67a41ea4/README.md
  role: primary
- resource: cann-recipes-raw/mindspeed-rl/adb494ad777ef4314bca717b56983feb67a41ea4/docs/zh/features/integrated_worker.md
  role: supporting
created_at: '2026-06-30T00:00:00Z'
updated_at: '2026-10-29T15:24:42Z'
platforms:
- agnostic
---

# TransferDock（RL 数据面：训推各 worker 间样本调度交换）

## Summary

TransferDock 是 [mindspeed-rl](../frameworks/mindspeed_rl.md) 一轮 GRPO/DAPO 迭代的**数据面**：rollout、reward、advantage、reference、actor 是逻辑 consumer，并不一一对应独立 Ray worker：ActorHybridWorker 同时实现生成、logprob 与更新，IntegratedWorker 可再合并模型角色共卡分时复用；规则奖励由独立 RuleReward actor 执行，advantage 由 CPU Ray task 计算。各消费者，彼此之间不直接传数据，而是统一向一个 **`GRPOTransferDock` Ray actor** 取放样本。它把一批样本组织成**列存**（每个字段一列，如 `prompts` / `responses` / `rm_scores` / `ref_log_prob` / `advantages`），用两张正交的状态矩阵——**数据就绪矩阵**（哪一列哪一行已被生产）与 **消费进度矩阵**（哪个 consumer 已取走哪一行）——驱动各阶段**按各自就绪条件异步流水**：dock 支持按所需列和批量的就绪条件取数；实际是否并发还受 trainer blocking、资源共用与同步点限制，不能由位图机制推导阶段同时运行。每个阶段是一个 **consumer**，独立维护自己的消费游标，因此同一行可被多个阶段先后取用、互不阻塞。取放接口是 `get_experience` / `put_experience`，配合 DAPO 的动态采样（zero-variance 组过滤）与 [partial-rollout](partial_rollout.md) 的续推/逐出在同一数据结构上落地。

> 训推态权重如何在同一批卡上 reshard/offload 见 [train-rollout-switch](train_rollout_switch.md)；TransferDock 管的是样本（experience）在各 worker 间怎么排队、就绪、被调度取走。

## 列存：一批样本 = 行 × 字段

`GRPOTransferDock`（继承 `TransferDock`）的核心是两个按列组织的字典，行数 `max_len = prompts_num × n_samples_per_prompt`——即「每个 prompt 采 `n_samples_per_prompt` 条响应」摊平成的样本总数。**连续 `n_samples_per_prompt` 行属于同一个 prompt 组**，这正是 GRPO 组内相对 advantage 的数据形状（算法见 [grpo-dapo](grpo_dapo.md)）。

```
experience_data        = {column: [None] * max_len}              # 每格存一条样本的变长 tensor
experience_data_status = {column: torch.zeros(max_len, int32)}   # 该格是否已被生产，1=ready
```

GRPO 的默认列覆盖一轮迭代的全部中间产物，按生产先后大致是：

`prompts` / `prompt_length` / `input_ids`（数据集灌入）→ `responses` / `response_length` / `attention_mask`（rollout 生成）→ `rm_scores` / `token_level_rewards`（reward 打分）→ `advantages` / `returns`（advantage 计算）→ `ref_log_prob`（reference 前向）→ `old_log_prob`（actor logprob，on-policy 下常被跳过）。数据集自带的额外字段（`dataset_additional_keys`），以及 DAPO 在 reward 阶段算出、由 DAPO trainer 硬编码进 `addition_columns` 的 `metric_for_dapo`，都经 `addition_columns` 动态追加成新列。每一格是该样本自己的变长 tensor，长度不齐——取数时才在 batch 维 `pad_sequence` 对齐（`padding_dict_to_tensor_dict`），所以列存里不存 padding，省显存也省序列化。

整个结构是一个 `@ray.remote(max_concurrency=100, num_cpus=10)` 的 Ray actor，常驻 CPU 侧；所有 worker 通过 `td.get_experience.remote(...)` / `td.put_experience.remote(...)` 远程访问同一份数据，由 `init_transfer_dock` / `sync_init_transfer_dock` 把这个 actor 句柄注入每个 worker。

## 两张状态矩阵：生产就绪 × 消费进度

调度完全由两组 int32 向量决定，二者正交：

- **数据就绪矩阵** `experience_data_status[column]`（每列一条、长度 `max_len`）——某行某列被 `_put` 写入后置 1。它回答「这条样本的这个字段生产好了没」。
- **消费进度矩阵** `experience_consumer_status[consumer]`（每个 consumer 一条、长度 `max_len`）——某行被该 consumer 取走后置 1。它回答「这个阶段把这条样本算过了没」。

consumer 即流水阶段，默认有 `actor_rollout` / `reward_scores` / `rule_reward` / `compute_advantage` / `ref_log_prob` / `actor_log_prob` / `actor_train` / `actor_image_embeds` / `trainer` / `grpo_metrics`，可经 `addition_consumers` 扩展。**每个阶段一条独立的消费向量**，意味着同一行样本被 rollout 写完后，reward、ref、train 各自从 0 开始消费它，彼此进度不相干——这是「同一份数据被多阶段异步复用」的关键：不需要把样本复制给每个阶段，只需各自记一条 bitmap。

每个 consumer 还配一把 `threading.Lock`（`consumer_sampling_lock`），因为 actor 的 `max_concurrency=100` 允许大量并发 `get_experience` 调用，取样与置位必须原子。

## get_experience / put_experience：按就绪条件取放

**放（`put_experience`）**：生产方把算出的 `{column: tensor/list}` 交给 dock，内部 `trans_input_to_experience` 拆成列与每样本 list，`_put` 逐格写入并把对应 `experience_data_status` 置 1。写入即「宣告就绪」，下游随之可见。

**取（`get_experience`）**：消费方传入 `consumer`、需要的 `experience_columns`、本次条数 `experience_count`，核心是 `_sample_ready_index`：

```python
not_consumed = experience_consumer_status[consumer] == 0           # 本阶段还没取过的行
data_ready   = all(experience_data_status[col] == 1 for col in columns)  # 所需列都已生产
usable       = (not_consumed & data_ready).nonzero()
if len(usable) < experience_count:
    return None        # 还不够一批，调用方稍后重试
```

凑够一批就选 `experience_count` 行（默认 `batch_balencing_sampler` 用 `torch.multinomial` 随机取；配 `use_dp_batch_balance` 时按 `prompt_length+response_length` 走 `batch_seqlen_balance_sampler` 做 DP 间序列长度均衡），把这些行的消费位 `consumer_status[sampled]=1`，再 `_get` 把各列对应格取出。`_get` 内 `_wait_for_data` 会自旋等到 `data_status==1`（超过 `timeout` 仅打印告警、不报错），因此即使生产稍滞后，取数也能阻塞等齐。返回 `(experience_batch, indexes)`——前者是 pad 好的 batch dict，后者是这批样本在 dock 中的行号，供消费方算完按行号 `put` 回结果。

**按组取**（`get_n_samples=True` 为 dock 接口默认值）：要求 `experience_count` 是 `n_samples_per_prompt` 的整数倍，把 `(max_len,)` 的两张矩阵 `reshape` 成 `(prompts_num, n_samples_per_prompt)`，**一个 prompt 的 `n` 条响应全部就绪才算这组可用**，整组一起取——保证按组消费时同一 prompt 的响应不被拆批。但 actor update、actor logprob 与 reference worker 显式按 partial-rollout 是否启用传入该参数：普通模式为 False，partial-rollout 模式才为 True。

## 按消费进度调度：阶段各跑各的

各 worker 的取数循环都是同一形状（以 actor 更新为例，`experience_count` 取自该阶段的 `rl_config.<stage>_dispatch_size`，如 `actor_rollout_dispatch_size` / `actor_logprob_dispatch_size` / `actor_update_dispatch_size`）：

```python
while self.all_consumed(experience_consumer_stage, ...) > 0:        # 该 consumer 还没消费完整批
    batch_data, index = self.dispatch_transfer_dock_data(stage, columns, experience_count, ...)
    ...                                                              # 计算
    self.collect_transfer_dock_data(output, index)                 # 结果 put 回 dock
```

`all_consumed(consumer)` 即 `experience_consumer_status[consumer].sum() == max_len`（partial rollout 下改判已完成组数 ≥ `GBS_train`）。于是每个阶段在自己的 while 里反复「取一批 dispatch 大小、算、写回」，直到把全批样本按本阶段消费完；`get_experience` 在数据不足时返回 `None` 让循环空转等待。就绪矩阵决定能不能取，消费矩阵决定是否还需取。`rl_config.blocking` 默认为 True，GRPO fit 还固定等待 `compute_advantage(blocking=True)` 完成后才下发 reference，并在 update 前等待模型任务结束；全共卡各态串行。只有在允许异步下发、资源可并行且 trainer 不设相应同步点时，dock 的就绪取数能力才可能形成阶段重叠。

dispatch/collect 是 worker 侧对 dock 的封装（`base_worker.py`）：只有各模型并行组的 leader 秩（TP/CP/PP rank 0，`rank_flg`）真正 `td.get_experience.remote` 触达 dock，取回的行号 `index` 经 `torch.distributed.broadcast` 同步给组内其余秩，样本本体经 `pack_experience_columns` 打包后用 HCCL 在组内广播。这是非 ZMQ 分支。默认 zmq_communication=True 时先走 dispatch_transfer_dock_data_zmq：行号通过 ZMQ 分发，正文小于10 MiB也走 ZMQ，较大正文才切到 HCCL。应按通信模式及大小判断，不把所有分发都概括为 HCCL。

## 动态采样接入：DAPO 的双库过滤

DAPO 的动态样本过滤（`filter_groups_enable`，按 metric_for_dapo 过滤指标无方差组，最终奖励含其他项时不保证优势为零；语义见 [grpo-dapo](grpo_dapo.md)）在数据面落成**两个 dock 串联**：DAPO 专用的 `DataStrategy.build_dapo`（`should_filter=True` 分支）构造一个 **采样库 `sampling_td`** 与一个 **主库 `td`**；GRPO 走 `build_grpo`、只建单一主库 `td`，无采样库。rollout 与 reward 把样本写进 `sampling_td`；`DynamicSampling.dynamic_sampling()` 以 `dynamic_sampling` 为 consumer 从 `sampling_td` **按组取**，对每组的 `metric_for_dapo` 算 `np.std`：

```python
for idx in range(0, experience_count, n_samples_per_prompt):
    metric_group = metric_values[idx: idx + n_samples_per_prompt]
    if np.std(metric_group) > 0 or len(metric_group) == 1:   # 组内有方差才保留
        kept_idx_list.extend(range(idx, idx + n_samples_per_prompt))
```

保留下来的组要写进主库的空位，行号由 `prefetch_request_index(n)` 给出——它在 `prefetch_request_index_lock` 下原子推进 `cur_index` 游标，返回一段连续行号供 `td.put_experience` 落位。之后 DAPO 的 advantage、可选 actor logprob 与 update 从主库消费；该算法 fit 不调用 reference 前向，ref 消费只属于使用它的算法。主库保留的是过滤指标有差异的组，不能据此保证每组最终梯度非零。一批过滤后若有效组不足，外层在未耗尽 filter_groups_max_batches 时继续 rollout 补采；达到上限仍不足时抛 ValueError("Generated too many")，仅配置为不限批次时才持续补采——这把 DAPO「首 step 多做几个 batch 推理补足有效样本」直接表达成两库间的搬运。`get_experience` 的 `allow_partial_ready_data`、`age`/`rollout_completed`/`global_ready_mask` 等字段服务于 [partial-rollout](partial_rollout.md) 的续推与按 age 重排。

## 多模态样本：MMGRPOTransferDock

多模态 RL 另起一个 `MMGRPOTransferDock`（同样是 Ray actor），与文本 dock 并列，存 `image` / `pixel_values` / `image_grid_thw` / `vit_embeds` / `position_ids` 等视觉列。它的存储粒度是 **prompt 而非样本**（构造时 `n_samples_per_prompt=1`），取数时按 `indexes // n_samples_per_prompt` 把样本行号折算回 prompt 行号——同一 prompt 的 `n` 条响应共享一份图像数据，不重复存。`consumer_columns` 给每个阶段声明它要的视觉列（如 `actor_rollout` 要原图、`actor_train` 要 `pixel_values`）；开 `reuse_image_embeds` 时把 `actor_rollout`/`actor_log_prob`/`ref_log_prob`/`actor_train` 的图像列整体换成预先算好的 `vit_embeds`，跳过重复的视觉编码。文本主库与多模态库由 worker 在 dispatch 时各取一份、`unpack_mm_experience` 还原后并进同一 batch。

## Evidence

- [README.md](../../../../../cann-recipes-raw/mindspeed-rl/adb494ad777ef4314bca717b56983feb67a41ea4/README.md)（primary）
- [integrated_worker.md](../../../../../cann-recipes-raw/mindspeed-rl/adb494ad777ef4314bca717b56983feb67a41ea4/docs/zh/features/integrated_worker.md)（supporting）

## Links

- [mindspeed-rl](../frameworks/mindspeed_rl.md)（TransferDock 的宿主框架；Ray 角色编排经此 dock + ZMQ 通信）
- [partial-rollout](partial_rollout.md)（复用 dock 的 `age`/`rollout_completed`/`global_ready_mask` 做续推与按 age 重排/逐出）
- [train-rollout-switch](train_rollout_switch.md)（训推态权重 reshard/offload；与本页样本调度互为 RL 一轮迭代的权重面与数据面）
- [grpo-dapo](grpo_dapo.md)（组采样的数据形状与 DAPO 动态过滤语义，由本 dock 在数据面落地）
- [rule-reward-verifier](rule_reward_verifier.md)（reward 阶段的无模型规则奖励，结果回写 TransferDock 的 rm_scores/metric 列）
