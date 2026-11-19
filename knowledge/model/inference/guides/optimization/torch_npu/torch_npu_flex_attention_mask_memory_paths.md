---
type: Guide
title: FlexAttention 掩码内存路径：条带构造、有界工作区与精确容量
description: 区分BlockMask构造峰值与前向byte-mask分配，记录静态workspace门槛、预算不截断以及精确容量回退。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
created_at: '2026-11-10T11:45:04Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FlexAttention 掩码内存路径：条带构造、有界工作区与精确容量

## 固定范围与两层内存问题

定向核对 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的共享 FlexAttention Python patch 和前向 sparse-mask 分配。发布版 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 缺少同路径 `torch_npu/_inductor/kernel/flex_attention.py`，本卡只作为主线候选。没有运行长序列、设备或性能实验，保持 `draft`、空平台。

创建 BlockMask 的临时 dense stripe，与编译前向为了部分可见块生成的 byte mask 是两层分配。前者优化构造时峰值，后者影响每次前向；[实际前向选路](torch_npu_flex_attention_forward_dispatch.md)的 mask-out 条件必须先成立，不能把两者当成同一个缓存或开关。

## BlockMask 在满足条件时分条带创建

`patch_flex_attention()` 包装 Python `create_block_mask`。只在编译区域外、`_compile=False`、NPU device、正整数 Q_LEN/KV_LEN 时选择 streaming；Dynamo compiling、编译式 mask 构造或非整数长度仍调用原函数。streaming 抛异常时记录告警并调用原始构造，不保证任意自定义 mask 都命中条带路径。

实现将未指定的 B/H 按 1 处理，以 `256 MiB // (B*H*KV_LEN*8)` 估计每条带的 Query 行数，再按 Q block 对齐且至少一个 block。逐条带调用原 `create_mask`，通过偏移后的 q_idx 保持全局位置，立即转换 partial/full block 表示并删除该 dense stripe，最终沿 Query block 轴拼接结果。

这没有一次性构造完整 dense [B,H,Q,KV]，但最终 partial/full 元数据仍随全图增长，列表和拼接也占内存。256 MiB 是公式里的目标估算值，不是整个构造的硬上限；至少一个 Query block 的限制也可能超过目标。不能由采用 streaming 推导长序列掩码永远不会 OOM。

## 静态工作区按可证明的上界分配

配置 `TORCHINDUCTOR_ASCEND_FLEX_ATTENTION_FWD_MASK_WORKSPACE_BYTES` 默认 256 MiB，经 int 后与 0 取最大。0 表示不使用这条预分配上界路线，而非关闭注意力或将 mask 容量强制设为零。Python FlexAttention 包装把该预算放入 kernel_options，使这个预算值进入 HOP/FX 识别的参数；不要把这条机制扩大成所有运行期策略都自动进入缓存键。

lowering 只在非 AOT、非多流调度，且 Q/K/V、kv_num_blocks、kv_indices 没有检测到动态维度时尝试静态工作区；两份元数据还必须都是 INT32。容量函数另要求：

- count shape 长度 3、index shape 长度 4，且前三维完全匹配；block_size 为两个维度，相关维度均大于零。
- 行数 rows=prod(count_shape) 不超过 4096。
- capacity=rows*index_shape[-1]，byte-mask 元素数 capacity*Q_BLOCK*KV_BLOCK 不超过 INT32_MAX，也不超过预算。

这依赖有效 BlockMask 的每行 count 不超过 index 最后一维。**预算不足返回 None 并转精确容量路线，不会把 capacity 截断到预算大小而丢弃块。** 只看 workspace capacity 有值，不能证明损坏的 count/index 内容已被完整校验。

静态路线由设备 offset kernel 生成各行偏移；活跃块数仍由设备元数据决定，上界容量可以大于实际块数。该实现以更稳定的 shape 容量换取潜在空闲空间，不等于按活跃块数精确分配。

## 精确容量与附加映射同样有成本

不满足静态门槛、预算不足或预算为零时，mask-out 分支构造 compact offsets 和 total_blocks，并以受约束的 unbacked size 表达实际块数。它为上界/运行期值添加 INT32 相关范围检查；这不是放任任意大规模索引或把运行期标量变成静态常量的保证。

两条路线随后都会分配 flat_to_row、flat_to_blk 两份 INT32 映射，以及 `[mask_capacity,Q_BLOCK,KV_BLOCK]` 的 INT8 mask，还有 offsets 等状态。因此预算比较的是 byte-mask 的元素字节数，不是整个前向的总临时内存上限：仅两份映射就额外约占 `8*mask_capacity` 字节，未计对齐和其他张量。

使用精确容量并不代表不需要前缀扫描、动态标量或映射生成；本卡没有追完这些 IR 在各 wrapper 下的全部 Host/Device 开销。工作区路线也不把完整 mask 内容跨调用缓存；规则或捕获数据变化仍按[BlockMask复用约束](torch_npu_inductor_flex_attention.md)处理。

定位时将构造阶段峰值、工作区预算/容量日志、实际元数据、mask-out选路和前向临时映射分开记录。逐项对照长序列、稀疏度和 batch/head 广播，验证注意力结果后再评价容量稳定与内存代价，不根据配置名宣称提速或显存已减少。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation）
