---
type: Concept
title: Swap Optimizer（优化器状态卸载 Host 内存）
description: TorchTitan NovaSwap 对 DistMuon/FlexShard 与 AdamW flat bucket 的状态搬运、预取依赖和 DCP 恢复；同时保留 MindSpeed master-weight swap 及 times=0 的独立实现。
tags:
- task.optimization
- topic.parallelism
- topic.memory
- topic.optimizer
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/common/optimizer.py
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/muon_optimizer.md
  role: supporting
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/developer_guides/checkpoint.md
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/optimizer/swap_optimizer/swap_optimizer.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/features_manager/optimizer/swap_optimizer_feature.py
  role: implementation
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:24:42Z'
platforms:
- a3
---

# Swap Optimizer（NovaSwap 状态卸载）

## Summary

当前 TorchTitan NPU 的 `optimizer.swap_optimizer` override 使用 NovaSwap 管理 Host/NPU 状态：DistMuon 的 momentum_buffer 按 FlexShard bucket 预取与卸载，AdamW 的 moments 按连续 flat bucket 搬运。不是旧版 `SwapOptimizersContainer`、全局 Adam.step 替换和 `swap_optimizer_times` 配置入口。

## 显式开启与范围

向现有 `override.imports` 追加 `torchtitan_npu.override.common.optimizer.swap_optimizer`，而不是设置 `swap_optimizer=true`。它与 Virtual Optimizer 替换相同 Config，不能同时启用。容器分别识别 DistMuon 与 AdamW；不能据类名推断所有 optimizer 都会被卸载。若配置已选择 CPU-offload optimizer，factory 会转给 CPU-offload 路线；HostSparse 配置另派生保留其生命周期的容器。

当前文档覆盖 DSV4 单机8卡、TP=PP=1、EP/DP-shard 训练；TP/PP>1、跨 world size 恢复和复杂拓扑未获同等验证。

## AdamW flat bucket

首次真正有梯度时懒规划状态；按 parameter group、device、dtype 和目标字节数分桶。当前内部常量以本批待初始化状态字节数除16规划，整参数不可拆，最大单参数可能大于目标桶；它不是可配置的旧 times 字段。bucket 中 exp_avg、exp_avg_sq（AMSGrad另有 max_exp_avg_sq）是连续 flat storage 的视图，DTensor 保留原分片元数据。

已有 bucket 执行 H2D→WAIT_DEVICE→原 PyTorch AdamW 更新→D2H，并在本桶更新前提交下一桶 H2D。驻留预算按3倍目标/最大桶字节数计，必要时等待旧桶释放；不能声称全量 moments 始终同时位于 device。首次分配的新桶先更新再卸载，不需先从 Host 取回。

wrapper 是 optimizer 实例级的，公共 step hook 保持每个逻辑 step 一次，桶内调用不会重复触发外部 hook。要求 differentiable=False、foreach=False；step scalar 的 CPU/device 位置遵循 fused/capturable 设置，不随 moments 一律卸载。

## Muon 与通信依赖

momentum_buffer 首次创建时注册唯一 NovaSwap 名称并 D2H。后续在 FlexShard storage-to-compute enqueue 之前提交该 bucket 的 H2D，每个 tensor 在 `_prepare_local` 仍 WAIT_DEVICE；transfer stream 提交 prepare/pack/inbound A2A 后，才在同一流提交已更新 redistributed momentum 的 D2H。caller 等待 compute_input_ready 后做 Newton–Schulz，可以与后一桶搬运重叠。

unredistributed items 不走该 A2A；在 caller stream 上准备、计算和更新后，沿单 tensor 路径卸载。不得删掉这些事件依赖，也不能继续写“Muon 与 Swap 互斥”。

## Checkpoint

state_dict 把被卸载状态替换为可供 DCP 访问的 CPU checkpoint views，包含 DTensor 全局元数据。未创建的 AdamW state 逐桶补齐，**不通过零梯度 step 伪初始化**，避免错误增加 step 和改变 bias correction。load 写入这些 destinations 后恢复原状态引用与参数名，并刷新 AdamW bucket 的 group 关联。

当前支持同步以及 CPU snapshot 的 async；`supports_async_with_pinned_mem=False`，不能把后者当作同等支持。恢复验收要检查 moments/step/参数组及后续真实更新，不能只检查 checkpoint 文件存在。

## MindSpeed Swap Optimizer 实现

MindSpeed 使用 `SwapDistributedOptimizer`；两条实现同属「前反向期间把优化器侧 FP32 状态卸到 Host、step 内以切片流水换回」的思路；但 MindSpeed 直接长在 **Megatron 分布式优化器**上，卸载对象更全、更新算子也不同。整体显存账见 [optimizer-memory](optimizer_memory.md)，框架侧见 [mindspeed](../frameworks/mindspeed.md)。

### 注入点与适用约束

`SwapOptimizerFeature`（开关 `--swap-optimizer`）在 optimizer 名含 `adam`（即 `--optimizer-selection fused_adamw`）时，把 `megatron.core.optimizer.distrib_optimizer.DistributedOptimizer` 整类替换为 `SwapDistributedOptimizer`，并把 `mindspeed.core.optimizer.adamw.AdamW.step` 换成 `swap_adamw_step`。仅在开启分布式优化器（`--use-distributed-optimizer` 或 `--use-layer-wise-distributed-optimizer`）时可用，否则 `validate_args` 直接抛错；与 `--reuse-fp32-param`、fused ema adamw 互斥。Muon 优化器走另一条 `swap_muon` 路径，不复用本类。`--swap-optimizer-times` 默认 16，越小则单批换得越大、并行越多、性能劣化越小但峰值越高。

### 卸载三类张量（与 torchtitan 的关键差异）

Megatron 分布式优化器里每个 fp16/bf16 模型权重对应一份 **FP32 master 副本**（`shard_fp32_from_float16`），AdamW 又为它维护 `exp_avg` / `exp_avg_sq` 两个 FP32 动量——合计 `参数量 × 12` Bytes 在前反向期间纯属占用。MindSpeed 把这三者**全部**卸到 Host pinned 内存：`create_tensor_maps` 给 fp16/bf16 主参数建 `cpu_state = {'param': pinned}`，`init_param_opt_state` 再给两动量各建 pinned 副本；device 侧一律 `storage().resize_(0)` 只留逻辑视图。这是与 torchtitan 的最大区别——torchtitan 权重由 FSDP2 以 DTensor 管理、optimizer 里没有独立 master 权重，故只卸两个动量。纯 FP32 模型参数（`shard_fp32_groups`）落入 `no_swap_params`：权重本体前反向要用、不卸，只卸其优化器状态。

### 初始化即随建随卸

`_build_model_and_main_param_groups` 每 clone 出一份 `shard_main_param` 就立刻 `swap_tensors_to_host`，避免建满整组 master 权重时冲击峰值（只发生在初始化，性能影响可忽略）。`init_param_opt_state` 给动量建 device 占位、copy 进 pinned CPU 后随即 `resize_(0)`。`swap_numel = swap_num // swap_optimizer_times`（`swap_num` 为全部 master 参数元素数）即整参数装批阈值（不是硬上限）；构造时按 `swap_num × 12 / MB` 打印本卡卸载量。

### step 三流水：预取 → 更新 → 回拷 → 卸载

`swap_adamw_step` 顺序遍历 `param_to_group_map`，靠两条 stream（`swap_to_device_stream` / `swap_to_host_stream`）加三组 event map（`swap_to_device` / `copy_to_model_param` / `swap_to_host`）串联依赖：

- **预取**：仅在 `swap_count == 0`（缓冲消费空）时，在 device stream 上 `wait_stream(swap_to_host_stream)` 后一次性 `swap_tensors_to_device` 预取累计 numel 逼近 `swap_numel` 的一批 master 参数 + 动量（`resize_` 回真实大小再 `copy_`，`non_blocking`）。
- **更新**：主流先 `wait_swap_to_device_event(param)`，再调 **`npu_apply_fused_adamw_v2`**（NPU 自研融合 AdamW kernel，区别于 TorchTitan 当前调用的 PyTorch AdamW step）原地更新 master 参数与两动量。
- **回拷**：`copy_tensor_to_model_param` 把更新后的 FP32 master 写回 bf16 模型权重，record 一个 `copy_to_model_param` event——这一步是 master-weight 设计独有，torchtitan 无此环节。
- **卸载**：在 host stream 上 `wait_copy_to_model_event(param)` 等回拷完成，`swap_count -= numel` 腾缓冲触发下一轮预取，再 `swap_tensors_to_host` 把 master 参数 + 动量写回 pinned CPU 并 `resize_(0)` 释显存。

由此 master 权重既要从 host 取回更新、又要在更新后回写 bf16 权重再卸回 host，比 torchtitan「只搬动量」多一条 master↔model 回拷链；第二轮 d2h 须等前一轮 h2d 结束再下发以保异步拷贝时序正确。

### Checkpoint 走 Megatron DP-zero

不依赖 torchtitan 的 DCP。`get_parameter_state_dp_zero` 收集 DP rank0 全量状态时，对已卸载参数直接从 `param_to_cpu_states_map` 取 host 真值（`tensors = param_to_cpu_states_map[main_param]`）而非读 device；`load_parameter_state_from_dp_zero` 回写时，若某 state 的 device storage 为 0 就把值写进对应 `cpu_state[key]`，维持「真值在 host、device 是空壳」的可续训态。


### 当前 times=0 分支

`swap_optimizer_times=0` 不再发生除零：阈值取全部 master 参数量，参数按 numel 降序，step_count 协调多个 optimizer 的首轮同步；deferred D2H 对待释放张量 record_stream 后再释放 storage。这是不同于正数分批的时序，不能把“越小单批越大”的经验外推成零值与正值完全同一模式。

## Evidence

- [optimizer.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/common/optimizer.py)（primary）
- [muon_optimizer.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/muon_optimizer.md)（supporting）
- [checkpoint.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/developer_guides/checkpoint.md)（supporting）
- [swap_optimizer.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/optimizer/swap_optimizer/swap_optimizer.py)（implementation）
- [swap_optimizer_feature.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/features_manager/optimizer/swap_optimizer_feature.py)（implementation）

## Links

- [Virtual Optimizer](virtual_optimizer.md)
- [Muon](muon_optimizer.md)
- [优化器显存治理](optimizer_memory.md)
- [检查点](checkpoint_dcp_hf.md)
