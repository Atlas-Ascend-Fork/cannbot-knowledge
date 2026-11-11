---
type: Optimization
title: "Chunked/SSM Cube 内核的『调用/指令条数』受限消除链（K 维融合 + 列组瓦片 + 行主序紧凑布局 + AIC gemm 合并）"
description: "MIX(Cube+Vector) 实现的 chunk-scan/SSM 类内核，块内 matmul 维度极小时，瓶颈既不是算力也不是带宽，而是 Cube 调用次数与向量指令/搬运条数。四步链消除：K 维融合、列组瓦片、行主序紧凑布局、AIC gemm 合并与屏障削减。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.data_movement.layout_transform
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X80: 调用/指令条数受限消除链（Cube chunk-scan 内核）

## 判定信号

profiling 出现下面任一组合，即可判为「调用/指令条数受限」而非算力/带宽受限：

- MIX 内核 `aic_mac` 极低，而 `aic_mte2 + aic_fixpipe >= duration`（串行）；
- AIV 侧 `aiv_scalar + aiv_mte2 + aiv_mte3` 超过 `aiv_time` 一半，但该 shape 的数据量远小于耗时；
- 块内 matmul 维度极小（N 或 K <= 16~64），`MatmulImpl::IterateAll` 调用次数与 `ch x kNum x 4` 同量级。

判据的本质：**固定开销 x 调用次数** 主导，而不是「每个操作有多慢」。

## 核心思路（四步链，建议按此顺序）

### Step 1 — K 维融合（收益最大）
把 pack 产出的 kNum 个 K 块拼成一个 `[rows, K]` tile，让每个块内 matmul 由 `[BT,BT]x[BT,BK=16]`
变成 `[BT,BT]x[BT,K(64/128)]`。AIC 的 IterateAll 次数从 `ch x kNum x 4` 降到 `ch x 4`。

> ★ **必须先对齐三处，否则静默算错**：host tiling 的 N=K、kernel 侧 `SetSingleShape(bt, K, bt)`、
> **以及 `SetOrgShape` / 单核 N（ldb）**。只改 host 的 `SetShape` 而不改 ldb 是常见失败模式；
> 而用 B 全 1 的退化输入做探针会掩盖 ldb 错误 —— **探针必须是随机满值输入**。

### Step 2 — 列组瓦片 `[BT,W]`
向量粒度从 `[BT,16]` 升到 `[BT,W]`，`W` 取 `min(kNum, 4096/(BT*16))`（瓦片 <=4096 元素）。
所有逐元素算子与每次搬运由此变成 1 条大操作。

### Step 3 — 紧凑布局改行主序 `[NCH,BT,K]`
原 `[NTK,BT,16]`（kb 主序）下，列组搬运无法表达为单条多块 `DataCopyParams`。
改成 `[NCH,BT,K]`（chunk 行主序）后，pack/unpack 从「每 chunk kNum 次小搬运」降为「每张量 1 读 1 写」，
列组搬运成为单条 `DataCopyParams`（`srcStride` 携带行 stride）。

### Step 4 — AIC gemm 合并 + 屏障削减
- A 面板改 `[nch, 2BT, BT]`（aq/ak 竖直相邻）=> 一次 `M=2BT` gemm 算 C1|C2；同一面板 `isTransposeA` 得 `[aqT|akT]`（K 维 2BT）再算 C3+C4。**4 gemm -> 2**，wsC 面板 4->3、B 面板 MTE2 装载 4->2 次、workspace 相应减少。
- AIV 屏障改「**一次发齐 MTE2 -> 纯 V 段 -> 批量 MTE3**」三段式：同管道相邻操作无需屏障（V->V、异缓冲 MTE2->MTE2 都不需要），每组 `PipeBarrier<PIPE_ALL>` 大幅减少到三段式所需的少数几条。

## 关键坑

1. **`SetOrgShape`/ldb 必须与 K 融合同步**（见 Step 1 的 ★）。退化输入探针会掩盖该错误。
2. **每次 Cube 调用的固定开销与调用次数严格线性** —— 所以「先放大单次调用规模（K 融合）」再做「替换实现方式」；**顺序反了收益就没了**：在未融合的结构上手写 Mmad 收益明显，K 融合后基本消失。
3. **手写 Mmad 在 910B2C 上受 L0B 装载路径限制**：唯一正确路径是逐 `[bt,16]` 切片的
   `LoadData3DParamsV2`；n>16 的整条 L0B 装载（线性 `LoadData2D`、单条 `LoadData3D(n=K)`、
   `LoadData3DParamsV2Pro + fMatrixCtrl`）均失败并触发 aicore exception。
4. **不要为了并行度抬 AIC 核数**：超过任务数所需的 AIC 并行度会被 MIX 核 `SyncAll` 的核数成本吃掉，
   反而变慢。
5. **拆行/拆 t-block 在掩码已折进操作数后没有收益**：Cube 结构下掩码已在 pack 阶段乘进 A，
   拆行不减任何 MAC，只把 IterateAll 次数翻倍 => 此时主核是「调用次数受限」而非并行度受限。

## 适用场景

- MIX（Cube+Vector）实现、任务粒度 = (chunk/batch, head) 且块内 matmul 维度 <=64 的 chunk-scan / SSM / 线性注意力族；
- 出现「Cube 很闲但整核耗时高」或「AIV 指令条数远超数据量」的 profiling 特征；
- 与 X79 正交：X79 解决 host 侧布局 device task 数，X80 解决 kernel 内的调用/指令条数。

## 验证方法
- **性能**：在目标设备上对父变体与变体做同一时间窗口的 A/B（正反序至少两轮），
  以绝对时延和配对差值判断，不用跨窗口比值；每一步单独消融，确认收益顺序。
- **精度**：跑全量精度用例，逐元素对比参考实现；K 融合/布局折叠后用随机满值输入
  （不用全 1 退化输入）验证 ldb/stride 正确。
- **容量**：审计 L0C/L1/UB/workspace 预算（含 2BT 面板、wsC 与 pack/unpack 缓冲），
  用 `static_assert`/越界检查确认无静默覆写。
