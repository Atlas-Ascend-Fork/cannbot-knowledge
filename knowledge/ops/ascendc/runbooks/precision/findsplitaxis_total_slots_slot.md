---
type: "Runbook"
title: "FindSplitAxis 误传 total_slots 致 slot 翻倍"
description: "Broadcast 类算子 tiling 把 total_slots(=kPhysNodes*2) 当作 phys_nodes 传入 FindSplitAxis，函数内部再乘 2，per_buf_bytes 被腰斩一半、tile 循环翻倍，TilingData 写出值与内部切分粒度不一致。判别=对比外层 per_buf_bytes 与 FindSplitAxis 内部 per_buf_bytes 是否相等，并核查第 4 实参传的是 total_slots 还是 phys_nodes。"
tags: ["task.debugging", "topic.implementation.tiling", "topic.tiling"]
status: stable
sources: []
created_at: "2026-08-18T07:46:05Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# FindSplitAxis 误传 total_slots 致 slot 翻倍

## 现象

在为 Ascend950PR（DAV_3510，soc Ascend950PR_9579）开发 Broadcast 类元素级除法算子 xdivy（`z = x / y`）时，代码检视对 `operators/xdivy/op_host/arch35/xdivy_tiling_arch35.cpp` 做设计一致性检查，发现 `DoTilingAndSet<R>` 模板调用 `FindSplitAxis` 时第 4 个实参传错：调用方传入的是 `total_slots`（= `kPhysNodes * 2` = 10），而 `FindSplitAxis` 签名该位置是 `phys_nodes`。函数内部又做了一次 `total_slots = phys_nodes * 2`，于是内部 `total_slots` 变成 20，`per_buf_bytes = (ub_per_core / 20) & ~31` 被腰斩为正确值（基于 total_slots=10 的 25376）的一半（12672）。后果是 TilingData 里写出的 `per_buf_bytes=25376` 与 `FindSplitAxis` 内部用来切分的 `12672` 不一致：kernel 侧 `InitBuffer` 按 25376 分配、`half_elems` 按 25376 计算，但切分轴 `a_i/a_o` 基于 12672 得到，buffer 访问偏移与切分粒度错配，构成 partial case correctness 偏差。

## 适用场景

- **工程形态**：算子仓开发（ops-registry-invoke），tiling 层 `op_host/arch35/*_tiling_arch35.cpp` 的 `DoTilingAndSet` 模板与 `FindSplitAxis` 辅助函数。
- **API 路径**：`gert::TilingContext` → `XdivyTiling::DoTilingAndSet<R>` → `FindSplitAxis`；`pipe_.InitBuffer(buf_[i], per_buf_bytes)`（kernel 侧）。
- **验证过的平台与 CANN 版本**：Ascend950PR（DAV_3510，soc Ascend950PR_9579），CANN 9.1.0。仅做主机端代码检视（tool_result 保留数值验证）；上板 ST/UT 输出未在 trace 中以 tool_result 保留。
- **适用粒度**：`operator_family`——所有用 `kPhysNodes * 2` 推导 total_slots、再把 total_slots 误当 phys_nodes 传给内部辅助函数的 Broadcast/元素级 tiling 实现。
- **路线优先级**：`diagnostic_only`——本卡只给判别方法与根因解释；修复后的上板闭环信号未从 trace 恢复。
- **不适用或未验证场景**：非 Broadcast 范式（无 `kPhysNodes`/Ping-Pong DB slot 推导）的 tiling；其他 arch（非 arch35/DAV_3510）的 UB 容量与物理节点数未验证。

## 判别方法

**触发条件**（tool_observed 失败症状）：代码检视（tool_result，ISSUE-A 数值验证）发现 Broadcast 类算子 tiling 的 `per_buf_bytes` 在外层（写入 TilingData）与 `FindSplitAxis` 内部（用于切分轴推导）不相等：外层 25376、内部 12672，bf16 `per_buf_elems` 外层期望 6344、内部实际 3168，tile 大小约为正确值一半、主循环次数翻倍。

**可执行探针**：
1. 打开 `op_host/arch35/*_tiling_arch35.cpp`，定位 `DoTilingAndSet<R>` 中对 `FindSplitAxis` 的调用，核查第 4 个实参传的是 `total_slots`（已含 DB 倍数）还是 `kPhysNodes`/`phys_nodes`（原始物理量）。
2. 对比 `FindSplitAxis` 签名第 4 形参的语义（是否在函数内部做 `*2`）；若函数内部有 `total_slots = phys_nodes * 2`，则调用方必须传未乘 2 的 `phys_nodes`，传 `total_slots` 即重复扣减。
3. 用 `ub_per_core`、`dtype_size` 代入两条路径算 `per_buf_bytes = (ub_per_core / total_slots) & ~31LL`：外层（调用方）与 `FindSplitAxis` 内部若得到不同值，即坐实调用约定不一致。
4. 进一步核对 kernel 侧 `InitBuffer(buf_[i], per_buf_bytes)` 用的 `per_buf_bytes` 与 `FindSplitAxis` 推出的 `a_i/a_o` 切分粒度是否同源；不同源则 buffer 访问偏移与切分粒度错配。

**原始观测**（Ascend950PR/DAV_3510，代码检视 tool_result ISSUE-A，ub_per_core=253952、dtype_size=4 即 bf16 走 fp32 档）：
- 外层 `per_buf_bytes`（写入 TilingData）= floor(253952/10/32)*32 = 25376。
- `FindSplitAxis` 内部 `per_buf_bytes` = floor(253952/20/32)*32 = 12672。
- bf16 `per_buf_elems`：外层期望 25376/4=6344，内部实际 12672/4=3168。
- 缺陷代码（逐字取自 trace file_read 事件，`DoTilingAndSet<R>` 内）：

```cpp
int64_t total_slots = kPhysNodes * 2;
int64_t per_buf_bytes = (ub_per_core / total_slots) & ~31LL;

FindSplitAxis(max_bro_shape_, dtype_size_, ub_per_core, total_slots, tiling->split);
```

- `FindSplitAxis` 签名与内部（未改动，逐字取自 trace file_read）：

```cpp
bool FindSplitAxis(const std::vector<int64_t>& max_bro_shape,
    int64_t dtype_size, int64_t ub_per_core, int64_t phys_nodes, SplitResult& out)
{
    // total_slots = phys_nodes * 2 (all buffers open DB)
    int64_t total_slots = phys_nodes * 2;
    int64_t per_buf_bytes = (ub_per_core / total_slots) & ~31LL;
    int64_t per_buf_elems = per_buf_bytes / dtype_size;
    // ...按 per_buf_elems 推导 a_i / a_o / a_i_tail / axis
}
```

**机制解释**（根因分析，属 interpretation）：`DoTilingAndSet<R>` 把"已乘 2 的 total_slots"当作"未乘 2 的 phys_nodes"传入 `FindSplitAxis`，`FindSplitAxis` 内部又乘了一次 2，slot 数从 10 翻倍到 20，`per_buf_bytes` 被腰斩一半。根因是调用约定不一致——外层与辅助函数对同一个量（`phys_nodes` vs `total_slots`）做了重复的 `*2`。`per_buf_bytes` 在 TilingData（25376）与 `FindSplitAxis` 内部切分（12672）两处不同源，kernel 侧 `InitBuffer` 按 TilingData 的 25376 分配、`half_elems` 按 25376 计算，但切分轴 `a_i/a_o` 基于 12672 得到，buffer 访问偏移与切分粒度错配，对部分 shape 产生 correctness 偏差。修复方向是把第 4 实参从 `total_slots` 改为 `kPhysNodes`，让 `*2` 只在 `FindSplitAxis` 内部发生一次——但本卡不内联修复 recipe，只给判别与根因。

## 预防

- tiling 辅助函数的"已推导量"（`total_slots`）与"原始物理量"（`phys_nodes`）不要互换传入；调用方应传原始量，让辅助函数内部统一推导，避免重复 `*2`。
- 在 `DoTilingAndSet` 与 `FindSplitAxis` 之间加一条断言或日志：外层 `per_buf_bytes` 与 `FindSplitAxis` 内部 `per_buf_bytes` 必须相等，不等即报错。

## 失效边界

- Ascend950PR/DAV_3510（arch35）实测推导；其他 arch 的 `kPhysNodes`、UB 容量不同，需按各自 `PlatformAscendC` 探测值重算，未验证，推断可迁移。
- `kPhysNodes * 2` 这一 slot 推导假设所有 buffer 全开 DB（Ping-Pong）；若改为单缓冲或部分 buffer 不开 DB，`total_slots` 推导需同步调整，本卡的 `*2` 假设不再成立。

## 坏实践

- 把 `total_slots`（已含 DB 倍数）当作 `phys_nodes` 传入辅助函数，让辅助函数再乘一次——典型的"重复扣减"。

## 验证信号

- 代码检视 tool_result ISSUE-A 给出 per_buf_bytes 内外不一致：外层 25376、`FindSplitAxis` 内部 12672，bf16 `per_buf_elems` 外层 6344、内部 3168（来源平台:950；证据等级:tool_observed）
- 缺陷代码逐字可核：`DoTilingAndSet<R>` 内 `FindSplitAxis(..., total_slots, ...)` 与 `FindSplitAxis` 签名/内部 `total_slots = phys_nodes * 2` 均取自 trace file_read 事件（来源平台:950；证据等级:artifact_verified）

<!-- cannbot:related:start -->
## 相关

- [Broadcast（张量变换）](../../apis/simd_api/adv_api/tensor_transform/broadcast.md)（`exemplifies`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《Broadcast（张量变换）》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [303 D2 末轴分块破坏 no-Cast DAG x2 加载](broadcast_303_d2_last_axis_no_cast_dag_x2_missing.md)（`related`）：候选展示 host 切分参数错误放大广播工作量；本卡展示末轴切分改变每核 tile 索引后旧加载条件漏中间 tile。
- [Broadcast场景](../../guides/operator_practice/simd_operator_impl/vector_programming/broadcast_scenario.md)（`related`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《Broadcast场景》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [count超4096仅前4288元算正确的精度阈值](count_4096_4288.md)（`related`）：count超4096仅前4288元算正确的精度阈值：本卡尚未确认根因，但已观测 tiling 的 a_o/max_bro_shape异常；FindSplitAxis卡提供可执行的内外 per_buf_elems一致性探针，适合作为受限的下一步排查而非声称同根因。 目标卡《FindSplitAxis 误传 total_slots 致 slot 翻倍》补充：Broadcast 类算子 tiling 把 total_slots(=kPhysNodes*2) 当作 phys_nodes 传入 FindSplitAxis，函数内部再乘 2，per_buf_bytes 被腰斩一半、tile 循环翻倍，TilingData 写出值与内部切分粒度不一致。判别=对比外层 per_buf_bytes 与 FindSplitAxis 内部 per_buf_bytes 是否相等，并核查第 4 实参传的是 to
- [split.axis 未随 PadAndSqueeze 偏移致 507035](../compilation/split_axis_padandsqueeze_507035.md)（`related`）：两卡都定位 host 侧 FindSplitAxis 输入/坐标错误：本卡漏加前补维度 delta，候选把 total_slots 错传为 slot。
- [tmpBuffer 分配步长≠访问步长触发 UB 越界 341](../compilation/tmpbuffer_ub_341.md)（`related`）：tmpBuffer 分配步长≠访问步长触发 UB 越界 341 与《FindSplitAxis 误传 total_slots 致 slot 翻倍》的衔接是：四个案例都把 UB 预算、分块或对齐计算与实际访问跨度不一致定位为越界根因，可复用‘按访问类型和对齐重算最大偏移’的验证方法。
- [多核对齐切分](../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/multi_core_aligned_split.md)（`related`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《多核对齐切分》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [多核非对齐切分](../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/multi_core_unaligned_split.md)（`related`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《多核非对齐切分》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [高维切分API](../../guides/programming_guide/library_api/basic_api/interface_classification/high_dim_split_api.md)（`related`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《高维切分API》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [507035 C 超 per_buf_elems 致 Phase1 UB 越界](../compilation/datacopypad_phase1_chunk_loop_per_buf_elems_507035.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；FindSplitAxis 误传 total_slots 致 slot 翻倍正文说明“Broadcast 类算子 tiling 把 total_slots(=kPhysNodes*2) 当作 phys_nodes 传入 FindSplitAxis，函数内部再乘 2，per_buf_bytes 被腰斩一半、tile 循环翻倍，TilingData 写出值与内部切分粒”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
- [ACL 507035 — 完整 a0 统计缓冲超过 UB](../compilation/ub_slices_reduction_axis_scratch_buffers_507035.md)（`same_topic`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《ACL 507035 — 完整 a0 统计缓冲超过 UB》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [ACLNN 507015 — tiling UB 漏算 kIdxBuf 下溢](../compilation/aclnn_507015_tiling_ub_kidxbuf.md)（`same_topic`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《ACLNN 507015 — tiling UB 漏算 kIdxBuf 下溢》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [Host 缺 SetDataSize 致 TilingData 截断](host_setdatasize_tilingdata.md)（`same_topic`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《Host 缺 SetDataSize 致 TilingData 截断》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [TilingData 追加数据超额致 INVALID_TILING](../compilation/tilingdata_invalid_tiling.md)（`same_topic`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《TilingData 追加数据超额致 INVALID_TILING》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [低 rank 零填充致 count=0 用 td_->rank 非 RANK](rank_count_0_td_rank_rank.md)（`same_topic`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《低 rank 零填充致 count=0 用 td_->rank 非 RANK》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
<!-- cannbot:related:end -->
