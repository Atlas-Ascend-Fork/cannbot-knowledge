---
type: "Runbook"
title: "split.axis 未随 PadAndSqueeze 偏移致 507035"
description: "DoTilingAndSet 在 PadAndSqueeze 压缩后 shape 上跑 FindSplitAxis 得 split.axis，再前补 1 填充到 R 维时未把 split.axis 偏移 delta；rank<R 时切分轴指向 size-1 前导维，inner_count 爆涨越界 UB 触发 507035。可用跨用例 stride 对比证伪 loopSrcStride≥240 误诊、并用 host split.axis 与 R 维 shape 检查判别。"
tags: ["task.debugging", "topic.implementation.tiling"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: '2026-08-27T12:23:11Z'
platforms: ["950"]
---

# split.axis 未随 PadAndSqueeze 偏移致 507035

## 现象

在 Ascend950（dav-3510/950，CANN 9.1.0）上为 `softplus_v2_grad` 算子实现 RANK_4 分支 Kernel 后跑 aclnn ST 用例：38/48 通过、10 个失败。其中 9 个是 C05 形状 `[1,1024]⊗[256,1024]`（grad 广播到 feat），覆盖全部 9 个 dtype 组合，`aclrtSynchronizeStream` 返回 **error 507035（vector core exception）**，kernel 直接崩溃，无 mismatch 输出。开发者日志把根因记为「NDDMA `loopSrcStride≥240` 平台约束致 UB 越界」（2D NDDMA split axis stride 1024 超约束 `[0,240)`），建议改用 1D `DataCopyParams` 分段搬运绕过 NDDMA stride 约束。

复调时发现该诊断 **错误**：同批次 C06 `[1,16,1,56]⊗[8,16,56,56]` 的 `loopSrcStride=3136` 反而通过——若约束真是 `stride<240`，C06 不可能过。真正根因在 host 侧 `DoTilingAndSet` 的坐标系不一致，与 NDDMA stride 无关。

## 适用场景

- **工程形态**：op_host 侧 TilingFunc 实现（aclnn 算子仓开发，ops-registry-invoke 工作流）。
- **API 路径**：`IMPL_OP_OPTILING` → `DoTilingAndSet<kRank>` → 公共 `FindSplitAxis`/`MultiCoreSplit`，kernel 侧读 `td->split.axis` 决定 NDDMA `loopSize/loopSrcStride/loopDstStride` 与 `inner_count`。
- **验证过的平台与 CANN 版本**：Ascend950（dav-3510/950），CANN 9.1.0（实测 UB=253952 B，非标称 256 KB）。
- **适用粒度**：`operator_family`——任何走「PadAndSqueeze 压缩 → 再前补 1 填充到 R 维」的广播算子 TilingFunc 都可能踩此坑。
- **不适用/未验证场景**：rank==R（delta=0）天然不受影响（C01/C02/C06/C07 等 rank=4 用例即因此通过）；rank<R 但 split.axis 恰好落在真实大维的偶发场景可能不崩但搬运错。a2/a3 未验证。

## 判别方法

1. **触发信号**（tool_observed）：aclnn ST 在广播用例上 `aclrtSynchronizeStream` 返回 507035（vector core exception），kernel 直接崩溃、无 mismatch 输出；失败系统性集中在 rank<R（PadAndSqueeze 后被压缩）的广播形状上。
2. **可执行探针**：
   - **跨用例 stride 对比**：取同批次一个通过用例，核对其 NDDMA `loopSrcStride`。若通过用例的 stride 远大于「误诊约束」（如 C06 的 3136 >> 240）却仍 PASS，即可证伪「stride<240 平台约束」假设，排除 NDDMA stride 为根因。
   - **host 坐标检查**：在 `DoTilingAndSet` 内打印 `td->split.axis` 与填充到 R 维后的 `max_bro_shape`，核对 `split.axis` 是否落在 size 为 1 的前导填充维（即 `max_bro_shape[split.axis] == 1` 且 `split.axis < delta`）。
3. **原始观测**（tool_observed）：507035 系统性出现在 PadAndSqueeze 后 rank<R 的广播用例（C05 rank=2）上；rank==R 的用例（C06 rank=4）通过。该通过/失败分布与 `loopSrcStride` 数值大小不相关（C06 stride=3136 通过、C05 stride=1024 反崩），直接否定 stride 约束假设。
4. **解释**（root-cause 分析）：`DoTilingAndSet` 坐标管线不一致——先对输入 `PadAndSqueeze` 得压缩后 `max_bro_shape_`（C05 得 `[256,1024]`，rank=2），在**压缩** shape 上 `FindSplitAxis` 得 `split.axis`（C05 得 0），**最后**才前补 1 填充到 4D（`delta = R - rank = 2`），但 **`split.axis` 未同步加 `delta`**。于是 C05 的 `td->split.axis=0` 在填充后 4D `[1,1,256,1024]` 中指向 size-1 前导维；kernel 读 `inner_count = product(max_bro_shape[split.axis+1 .. R-1]) = 1*256*1024 = 262144`（应为 1024），`tile_elems = a_i_seg * inner_count ≈ 15*262144` 远超单 buffer 15872 元素 → UB 大规模越界 → 507035。这同时解释 C06 通过：C06 压缩后 rank=4、`delta=0`，split.axis 无需偏移，坐标系天然一致。关键换算：`per_buf_bytes = (ub/physNodes) & ~31 = (253952/4)&~31 = 63488`；`per_buf_elems = 63488/4 = 15872`；`a_i = 15872/1024 = 15`。

## 验证信号

- `cat docs/softplus_v2_grad/develop/LOG.md` 记载首实现 ST 38/48 PASS、10 FAIL，9× C05 `[1,1024]⊗[256,1024]` 报 `aclrtSynchronizeStream` error 507035，并记前序 `loopSrcStride≥240` 误诊（来源平台：950；证据等级：tool_observed）。

## 误诊

前序日志把 9× C05 崩溃归因为「NDDMA `loopSrcStride≥240` 平台约束」，建议「改用 1D `DataCopyParams` 分段搬运绕过 NDDMA stride 约束」。该归因 **错误**：C06 的 `loopSrcStride=3136`（远大于 240）却能通过，证伪「stride<240」假设。真正根因是 host 侧 split.axis 坐标系未随 PadAndSqueeze→R 维填充偏移 `delta`，导致 kernel 内 `inner_count` 爆涨、UB 越界。按误诊的 1D 分段搬运方案去改 kernel 属治标（绕开 NDDMA），治本应修 host `DoTilingAndSet` 坐标系。

## 失效边界

- 仅 Ascend950（CANN 9.1.0，UB=253952）实测；a2/a3 未验证，但「PadAndSqueeze 后 split.axis 坐标系偏移」是纯 host 逻辑问题，与平台无关，推断可迁移，落库前需在 a2/a3 复跑 C05 类用例确认。
- rank==R（delta=0）的算子天然不受影响。
- split.axis 深层的 `inner_count`/`tile_elems` 数值（262144、≈3.9M、15872）来自会话内 host debug-print 推算，非 trace 的 tool_result 直采，仅作解释，不作为独立可核信号。

## 坏实践

- 在 host 侧同时维护「压缩坐标系」与「R 维坐标系」两套 shape，但只对 shape 做填充、忘了对 `split.axis` 做对应 `delta` 偏移——这是坐标管线不一致的典型坑。
- 用「在 kernel 里 1D 分段搬运绕过 NDDMA stride 约束」去掩盖 host tiling 坐标 bug：治标不治本，且会引入不必要的 kernel 复杂度。