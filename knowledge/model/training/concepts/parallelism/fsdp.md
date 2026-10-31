---
type: Concept
title: FSDP2（Fully Sharded Data Parallel 2）
description: 当前 decoder/vision FSDP helper 的逐参数 mesh、expert Shard 选择、reshard、混合精度、绑权重与预取，以及 EP 通信域分离；区分来源内存案例与 MindSpeed/FSDPTurbo 路线。
tags:
- task.design
- topic.parallelism
- topic.mixture_of_experts
- topic.memory
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/torchtitan/distributed/fsdp.py
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/parallelize.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/sharding.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/config_registry.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/ep_process_group.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/docs/zh/features/custom_fsdp.md
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/docs/zh/features/fsdp2.md
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/distributed/custom_fsdp/param_and_grad_buffer.py
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/distributed/torch_fully_sharded_data_parallel/torch_fully_sharded_data_parallel_adaptor.py
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/pipeline_parallel/dualpipev/dualpipev_chunks.py
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/features_manager/pipeline_parallel/dualpipev_feature.py
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/fsdp/distributed/expert_parallel/expert_fully_shard_parallel.py
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/fsdp/distributed/fully_shard_parallel/fully_shard_parallel.py
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/fsdp/distributed/parallel_state.py
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/fsdp/mindspeed_parallel_engine.py
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/fsdp/parallel_engine_config.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/fsdp2/distributed/parallel_engine_config.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/docs/zh/guides/development/fsdp2_model_migration_guide.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:39:13Z'
platforms:
- a3
---

# FSDP2（参数分片、专家 mesh 与预取）

## Summary

FSDP2 用逐参数 DTensor 表示分片，计算前按需 AllGather、反向归约梯度，降低参数/梯度/优化器状态的常驻占用。前向后是否立即 reshard 由策略决定：always 更省显存，never 保留聚合参数以省反向通信，default 使用框架的场景规则。不能把“计算后始终释放”当成所有配置的行为。

## 当前 TorchTitan NPU 接入

V3.2 的 parallelize_deepseek_v3_2 直接复用社区 DeepSeek V3 parallelizer；本仓的 sharding.py 在通用 decoder/MTP 布局之上补 DSA Indexer 与 MLA 配置，不再使用旧 infra/parallelize.py 或静态 32K TOML。默认 V3.2 debugmodel 是 local batch4、seq2048、10步、EP1、FullAC；它不能作为671B多卡配置的同义入口。

extension `distributed/fsdp.py` 提供 decoder/vision FSDP helper：

- non-expert 参数使用 dp_mesh；EP>1 时 routed experts 使用 edp_mesh，按参数指定 mesh info，保留 HSDP replicate 轴。
- full_dtensor 通过显式 DataParallelMeshDims 告知哪些轴属于数据并行，避免凭 axis 名字猜测。
- experts 的 E/FSDP×EP 度大于专家数时使用 Shard(1)，否则 Shard(0)，避免 expert 轴 padding；不能一概说所有参数都沿0维分片。
- tied embedding/lm_head 作为同一 FSDP 单元，避免重复 AllGather；ignored_params 向各 shard 传递。普通层先包，再包根模块。
- MixedPrecisionPolicy 分别设置 param_dtype/reduce_dtype，并关闭自动 cast_forward_inputs；CPU offload 由 CPUOffloadPolicy 控制，vision helper 同样传入 offload policy。
- helper 显式关闭 FSDP 自带梯度除法，归一化由训练路径负责；不能再额外假定它总会按 mesh 大小除一次。

EP>1 时显式设置 embedding→blocks→norm/head 的前向预取和反向逆序预取，避免 EP 的 D2H 同步干扰隐式预取。通信能否被计算覆盖仍取决于带宽、分片形状与计算窗口。

## EP process group 与预取协同

当前导入 torchtitan_npu 时，真实 backend 且 EP>1 的路径自动分离 EP HCCL group，保留 dense/replicate/efsdp 的组与 ranks。spmd_types 在 sparse mesh 注册时替换 EP 轴；default/full_dtensor 在 dispatcher wiring 时传独立 mesh；fake 或 EP1 不建新组。DeepEP 的 ElasticBuffer 另用专用 group，不能把默认200MB误当实际通信 buffer 需求。

这解决特定拓扑下 FSDP 与 EP 共用 PG 导致 AllGather/ReduceScatter 和 AllToAll 串行的问题。来源 V4 案例报告等待约10ms→3ms、性能+1.1%；是该源实验的观测，不是当前任意拓扑的保证。

## 来源中的模型内存案例

最新 Recipes 优化文档仍记录 A3 的两组配置，用于理解选型，不能作为当前 registry 默认值：

- V3.2 671B 的 FP32 权重+梯度约5368GB，超32卡A3的4096GB总量，因此该设置使用64卡；这不是低精度、offload 或裁剪模型的通用最小卡数。非专家权重以 DP/FSDP 二次分片，例 `(671B-654B)/PP2/TP4*8Byte≈18GB` 再由 DP16 均摊，未计不参与TP的额外部分。
- V4 Flash 来源采用 TP/PP1、EP/FSDP128（64卡A3的128die）、MBS1/GBS1024，去掉TP/PP以减少耦合通信；文档给出的1100 tokens/p/s来自融合算子与AutoFuse累计配置，不能当成FSDP单项收益。
- 优化器态卸载可将给定FP32权重/梯度/Adam状态账从16字节/参数降至常驻约8字节，但仍有step期间桶与临时缓冲；当前入口是 [NovaSwap override](../techniques/swap_optimizer.md)，不再传旧布尔/times字段。

DTensor 以 Shard、Replicate、Partial 描述布局，自动重分布仍可能引入通信；只声明“不并行”不保证每个内部算子都零通信，应核对实际前反向图。

## MindSpeed 的三条 FSDP 落地路径

[mindspeed](../frameworks/mindspeed.md) 在 Megatron 训练栈上提供三条与 ZeRO-3 同源、实现各异的全分片数据并行：参数 / 梯度 / 优化器状态在 DP 域内切分，前向逐层 AllGather 收集完整权重、用毕即释放分片，反向 AllGather 后做 ReduceScatter 同步并只留本 rank 梯度分片。与上文 torchtitan-npu 把 FSDP2 绑定到 TorchTitan DTensor 模型与 Python Config 的做法不同，MindSpeed 的三条路径分别走 **Megatron FlatParameter 桶**、**包装 PyTorch FSDP2 的 yaml 适配层**、**声明式 ND 并行引擎**三种装配形态。

### Custom FSDP（FlatParameter 桶 + 分布式优化器）

`--use-custom-fsdp` 路径派生自 `megatron.core.distributed.custom_fsdp`，把一组参数展平拼接进 `ParamAndGradBuffer` 的桶（FlatParameter 风格，与下文 FSDP2 的逐参数 DTensor 相对）。梯度归约由 `mark_bucket_ready` 驱动：一个 bucket_group 内所有 bucket 就绪后，在独立的 `reduce_scatter_stream` 上用 `_coalescing_manager` 合并集合通信——`data_parallel_sharding_strategy == 'no_shard'` 时对整桶做 `all_reduce`，否则 `reduce_scatter_tensor` 得到本地 shard 再累加到 `local_buffer`，随后按 `BucketStatus` 状态机 `free_bucket_storage` 释放桶显存。归约 op 由 `gradient_reduce_preprocessing` 选定：`average_in_collective` 走 `ReduceOp.AVG`，否则 `ReduceOp.SUM` 配 `scaling_factor` 缩放（`gradient_reduce_div_fusion` 且非 bf16 时免乘）。

开启配置（关闭 `CUDA_DEVICE_MAX_CONNECTIONS`，且必须叠加分布式优化器）：

```bash
--use-custom-fsdp
--data-parallel-sharding-strategy optim_grads_params   # 权重+梯度+优化器状态全切
--no-gradient-accumulation-fusion
--use-distributed-optimizer
unset CUDA_DEVICE_MAX_CONNECTIONS
```

这一路是「基本功能」实现，不建议与仓上其他特性组合；权重与梯度被进一步切分换显存下降，但每次前反向新增 AllGather 通信，性能相应下降。

### torch-FSDP2 适配（包装 PyTorch fully_shard + DTensor）

PyTorch 的 FSDP1 把桶内参数展平为单个 `FlatParameter`，难以对单参数做冻结 / 精度转换等差异化操作，且 state-dict 逻辑复杂、需额外通信；FSDP2 移除 FlatParameter，改用**沿 0 维分片的 DTensor** 表示分片参数，支持单参数便捷操作与免通信的分片 state-dict。MindSpeed 经 `--use-torch-fsdp2 --fsdp2-config-path <yaml>` 包装 PyTorch `torch.distributed.fsdp.fully_shard`，注意 `CUDA_DEVICE_MAX_CONNECTIONS` 须设为 2（不能为 1），权重保存 `--ckpt-format` 仅支持 `torch_dist` / `torch_dcp`，并需关闭分布式优化器与 `--recompute-*` 系列重计算开关。

`Fsdp2Config`（yaml 反序列化）字段：

| 字段 | 含义 |
|------|------|
| `sharding_size` | 每个分片组的 NPU 数；`_create_device_mesh` 据副本维（`world_size // sharding_size`）分情形建网格：副本维=1 时建 1D `["Shard"]`（纯 FSDP），否则建 2D `["Replicate","Shard"]`（HSDP，分片域内分片、副本域间复制） |
| `sub_modules_to_wrap` | 要 `fully_shard` 包装的模块类（绝对路径引入，如 `mindspeed_mm...VideoDiTBlock`）；默认 `{TransformerLayer, LanguageModelEmbedding, RotaryEmbedding}` |
| `reshard_after_forward` | 前向后立即重分片（`bool`/`int`，与 torchtitan 的 `fsdp_reshard_after_forward` 同义） |
| `param_dtype` / `reduce_dtype` / `output_dtype` / `cast_forward_inputs` | 组装为 `MixedPrecisionPolicy`：AllGather 用低精度参数、梯度 ReduceScatter 用更高精度 |
| `offload_to_cpu` / `pin_memory` | `offload_to_cpu=True` 时用 `CPUOffloadPolicy(pin_memory=...)` 把权重/梯度/优化器状态卸载到 CPU，否则 `OffloadPolicy()` 不卸载 |
| `num_to_forward_prefetch` | 前向预取层数（默认 0） |
| `ignored_modules` / `recompute_modules` | 排除 FSDP 管理 / 走 `apply_activation_checkpointing` 重计算的模块类 |

装配在 `torch_fully_sharded_data_parallel_init`（Megatron `TorchFullyShardedDataParallel`）内：对模型做**后序遍历**，命中 `sub_modules_to_wrap` 的子模块自底向上逐个 `fully_shard`，最后包装 root 模块；再按 `num_to_forward_prefetch` / `recompute_modules` 显式设置 `set_modules_to_forward_prefetch` / `set_modules_to_backward_prefetch` 预取计划，避免重计算打乱默认调度。fp8 权重在包装前关闭 transpose cache、meta-device 初始化时 rank0 实例化后 `_broadcast_coalesced` 同步。`torch_dist` 续训要求模型实现 `sharded_state_dict()` 且所有权重 0 维 size ≥ `sharding_size`。针对 Llama-7B，FSDP2 相比 FSDP1 取得更高 MFU、峰值内存降低约 **7%**、损失曲线一致。[mindspeed-mm](../frameworks/mindspeed_mm.md) 的 **Megatron 桥接式 FSDP2** 走这条路径；新版插件式后端用 trainer.py/顶层YAML/fsdp_plan.apply_modules，是另一条装配路线。

### MindSpeedParallelEngine（声明式 ND 引擎，fsdp/efsdp 双网格）

`mindspeed/fsdp/` 的 `MindSpeedParallelEngine` 是 MindSpeed 自有的声明式 ND 并行引擎，构造时按固定序对模型装配：`apply_quantization_modules → apply_tp_modules → apply_ep_modules → apply_recompute_modules → apply_fsdp_modules`（FSDP 为最外层，与 torchtitan 装配顺序同构）。其切分由 `ParallelEngineConfig`（`FSDPPlanConfig` / `TPPlanConfig` / `EPPlanConfig` / `QuantizeConfig`）以**模式字符串声明**驱动，而非 TorchTitan 的 Python Config：`fsdp_plan.apply_modules` 形如 `{'model.layers.*': {reshard_after_forward, shard_placement_fn}}`，`fully_shard_parallel_modules` 据此 pattern-match 逐模块 `fully_shard` 并按 `num_to_forward_prefetch` / `num_to_backward_prefetch` 排预取。

`init_parallel_state` 通过 `init_device_mesh` 一次性建**两套设备网格**，与 torchtitan 的 `fsdp` / `efsdp` / `edp` mesh 命名直接对应：

| 网格 | mesh_dim_names | 用途 |
|------|----------------|------|
| 主网格 | `('dp', 'fsdp', 'cp', 'ulysses', 'tp')` | 非专家参数沿 `fsdp` 维全分片 |
| 专家网格 | `('edp', 'efsdp', 'ep')` | 专家经 EP 切分后，沿 `efsdp` 维对剩余 DP 做二次分片 |

`validate_fsdp_config` 把 EP 的 `apply_modules` 与 TP 的 colwise/rowwise 模块自动并入 FSDP 的 `ignored_modules`——即 FSDP 不再去切 TP/EP 已经切过的参数，只对剩余复制维全分片，正是上文 torchtitan「FSDP 作为最外层对剩余复制维做分片」的等价实现。专家二次分片由 `expert_fully_shard_modules` 落地：对每个专家 `fully_shard` 时传 `shard_placement_fn = lambda x: Shard(1)`（沿专家 dim 1 切），并 `set_gradient_divide_factor`，因子取 `expert_parallel_size × expert_fully_shard_parallel_size × expert_data_parallel_size`。`QuantizeConfig` 提供 FSDP **低精度 AllGather**（`fsdp_low_precision_all_gather_mode` ∈ `on-demand`/`all`，开重计算时强制 `all`），在收集权重时即以量化精度通信省带宽。MindSpeed-LLM 当前 FSDP/TP/Quantize/ChunkBatch plan 从 FSDPTurbo 基类继承，已不再简单镜像此处全部 dataclass；CP 接受 ring、ulysses、kvallgather，量化字段使用 quant_recipe 并设置 fsdp_world_size。EP gradient_divide_factor 可显式给定，未设时用实际 world size，不等于旧私有字段的固定乘积。

```mermaid
flowchart LR
  Q["量化转换<br/>低精度 AllGather"] --> TP["TP<br/>colwise/rowwise"]
  TP --> EP["EP<br/>experts 沿 ep 切"]
  EP --> RC["重计算"]
  RC --> F["FSDP（最外层）<br/>fsdp 切非专家 / efsdp 切专家"]
```

### 三条路径与 torchtitan FSDP2 对照

| 维度 | Custom FSDP | torch-FSDP2 适配 | MindSpeedParallelEngine | torchtitan-npu FSDP2 |
|------|-------------|------------------|--------------------------|-----------------------|
| 分片表示 | FlatParameter 桶（Megatron buffer） | DTensor（0 维分片，PyTorch FSDP2） | DTensor（PyTorch FSDP2） | DTensor（PyTorch FSDP2） |
| 入口 | `--use-custom-fsdp` + 分布式优化器 | `--use-torch-fsdp2 --fsdp2-config-path` | `MindSpeedParallelEngine(config, model)` | Python Config + decoder FSDP helper |
| 切分声明 | DDP 策略 `optim_grads_params` | yaml `Fsdp2Config` + `sub_modules_to_wrap` | 模式字符串 `apply_modules` plan | TorchTitan ParallelStyle plan |
| 专家二次分片 | — | — | `efsdp` 网格 + `Shard(1)` | `edp_mesh` 网格 |
| 配套约束 | 必须开分布式优化器 | 关分布式优化器/重计算，`torch_dist` ckpt | 与 TP/EP 互斥切分（ignored_modules 自动合并） | 逐参数 mesh 与 reshard policy 由当前 decoder helper 接收 |

[DualPipeV](dualpipev.md) 分块代码虽保留按 use_torch_fsdp2/use_custom_fsdp 选择包装类的分支，但固定版本 DualpipeVFeature.validate_args 会在 use_custom_fsdp=True 时先抛不兼容断言。因此 custom-fsdp 分支存在不代表组合可用；其余包装也需经过各自参数校验，不能只凭分支认定已支持。


## 验证边界

分别核对参数与梯度的本地 shard、dense/expert mesh、梯度归一、绑权重、reshard policy、prefetch 和 checkpoint 恢复。FSDP2 与 ZeRO-3 思路相近，不能据此宣称不同框架的 DualPipeV、optimizer 或 CP 任意组合可用。

## Evidence

- [fsdp.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/torchtitan/distributed/fsdp.py)（primary）
- [parallelize.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/parallelize.py)（implementation）
- [sharding.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/sharding.py)（implementation）
- [config_registry.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/config_registry.py)（implementation）
- [ep_process_group.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/ep_process_group.md)（supporting）
- [deepseek-v32_pre_train_optimization.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md)（supporting）
- [deepseek-v4_torchtitan_npu_autofuse.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md)（supporting）
- [custom_fsdp.md](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/docs/zh/features/custom_fsdp.md)（supporting）
- [fsdp2.md](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/docs/zh/features/fsdp2.md)（supporting）
- [param_and_grad_buffer.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/distributed/custom_fsdp/param_and_grad_buffer.py)（supporting）
- [torch_fully_sharded_data_parallel_adaptor.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/distributed/torch_fully_sharded_data_parallel/torch_fully_sharded_data_parallel_adaptor.py)（supporting）
- [dualpipev_chunks.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/pipeline_parallel/dualpipev/dualpipev_chunks.py)（supporting）
- [dualpipev_feature.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/features_manager/pipeline_parallel/dualpipev_feature.py)（supporting）
- [expert_fully_shard_parallel.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/fsdp/distributed/expert_parallel/expert_fully_shard_parallel.py)（supporting）
- [fully_shard_parallel.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/fsdp/distributed/fully_shard_parallel/fully_shard_parallel.py)（supporting）
- [parallel_state.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/fsdp/distributed/parallel_state.py)（supporting）
- [mindspeed_parallel_engine.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/fsdp/mindspeed_parallel_engine.py)（supporting）
- [parallel_engine_config.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/fsdp/parallel_engine_config.py)（supporting）
- [parallel_engine_config.py](../../../../../cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/fsdp2/distributed/parallel_engine_config.py)（supporting）
- [fsdp2_model_migration_guide.md](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/docs/zh/guides/development/fsdp2_model_migration_guide.md)（supporting）

## Links

- [TorchTitan 多维布局](torchtitan_5d_parallel.md)
- [训练 CP](custom_cp_dsa.md)
- [MindSpeed-MM](../frameworks/mindspeed_mm.md)
- [Swap Optimizer](../techniques/swap_optimizer.md)
