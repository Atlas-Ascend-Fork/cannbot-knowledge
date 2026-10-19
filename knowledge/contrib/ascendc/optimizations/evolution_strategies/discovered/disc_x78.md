---
type: Optimization
title: "逐 token 串行 scan 的标量归约链清零（Scalar-Free Reduction：分组 WholeReduceSum 保序归约 + 归约块 DMA 合并 + 去 per-task 全屏障）"
description: "在逐 token 串行 scan（每 token 沿状态维做若干次归约）的向量核里，最贵的往往不是向量体，而是挂在 epilogue/token 循环里的标量归约链：for (i < L) s += buf.GetValue(i); 形态。"
tags:
  - task.optimization
  - topic.compute.reduction
  - topic.implementation.synchronization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X78: 逐 token 串行 scan 的标量归约链清零

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X78
> title: "逐 token 串行 scan 的标量归约链清零（Scalar-Free Reduction：分组 WholeReduceSum 保序归约 + 归约块 DMA 合并 + 去 per-task 全屏障）"
> origin: discovered
> discovered_round: 1
> discovered_from: "Mamba2Bwd evolution, round_1/parallel_2 (node x0, open_exploration)"
> base_speedup: "同窗 A/B（同一 device、同一窗口、同一 warmup/retry）pristine 1048.31us -> 781.61us = 1.341x；vs PyTorch geomean 14.34x -> 19.23x；Σasc 239566 -> 177881us (-25.7%)"
> confidence: single_op
> status: active
> op_families: [ssm, chunk-scan, reduction, elementwise, recurrent]
> bottlenecks: [scalar_compute, scalar_reduce_after_vector, no_overlap, sync_overhead, undersize_transfer]
> tags: [scalar-chain, whole-reduce-sum, per-token-scan, reduction-association, precision-floor, bf16-output, block-dma, pipe-barrier, 910b2c, dav-c220, mamba2, reverse-adjoint]
> strategy_ids: [X78, P94, X2, P66, P1]
> ```

## 核心思路

在**逐 token 串行 scan**（每 token 沿状态维做若干次归约）的向量核里，最贵的往往不是向量体，而是
挂在 epilogue/token 循环里的**标量归约链**：`for (i < L) s += buf.GetValue(i);` 形态。
它不是「L 条独立 load」，而是一条 **L 长、不可并行的标量 FADD 依赖链**（≈4 cyc/项）；
当 L ≈ 归约维长度（本算子 NP/PP，最大 176）且每 token 调用 2 次时，这条链的长度与整个 token 的
向量指令体（~880 repeat）**同量级** —— 于是它成了全核关键路径，而 profiling 的向量占比看起来仍很健康。

X78 的做法（三步，全部不改数值语义）：

1. **标量链 → 定长分组向量归约（保持顺序）**：把连续归约缓冲按 **64 元素**切成 G = ceil(L/64) 组，
   每组一条 `WholeReduceSum<float, true>(grp, buf, /*mask 全 1*/ , G, 1, 1, /*dstStride>>3*/ 8)`
   （repeat 序 = 组升序 ⇒ 组内与组间都是**同一顺序**的逐元素累加），标量侧只剩
   `for (g < G) s += grp.GetValue(g);` ≤3 次读。
   ⇒ 标量链从 L≈176 降到 ≤3，**结合序与逐元素实现逐位一致**（bf16/fp32 输出都不变）。
   前提：被归约缓冲尾部必须**零填充到 64 的倍数**，否则分组会读进相邻缓冲的脏值。
2. **归约块 DMA 合并**：跨头/跨 batch 的「每头一次小 DMA + 逐次握手」改成**一次 [R, NP] 整块 DMA**
   载入后本地树归约（搬运次数 ratio -> 1，且合并后搬运宽度满足 512B 对齐更友好）。
3. **去掉 per-task 全屏障**：`for (h) { PipeBarrier<PIPE_ALL>(); ...SetValue(h, GM.GetValue(...)) }`
   这类「每行一次全流水线栅栏」在每 task 内重复 H 次，改为整行批量读入 UB 后一次 cast/写回。

## 适用场景

- **逐 token / 逐 step 串行 scan** 的向量核（SSM/线性递归反向伴随、chunk-scan、scan-based norm 等），
  其 per-token 归约维长度 L ≳ 64（归约链长度与向量体可比）；
- 归约结果只用于**标量**（如 draw/scale 因子）或少量元素的场景 —— 这类归约最容易被写成 `GetValue` 循环；
- bf16/fp16 输出 + fp32 中间量的算子（此时**必须**保序，见下）。

## 实现要点 / 红线

- **顺序不可改**：任何把「顺序累加」换成「折半树 / 分组树」的实现都会改变结合序。
  本算子上实测：折半树列归约**再快 1.44x**（544.6us），但把 `dC`（bf16 输出）的 MARE 从 5.3e-3
  推到 **0.42**（阈值 7.8e-3）—— 见 failure pattern f19。**收益让位于精度**。
- 分组归约的 mask 用**位掩码**（`uint64_t[2]`）而非计数形式；缓冲尾部零填充到 64 倍数。
- 归约块 DMA 合并后仍要保持「原逐头顺序」，否则同样改序。
- UB 预算：分组缓冲 + 整块 DMA 缓冲需要额外 UB，先算 `PP/NP=128` 的最坏情形。

## 来源

Mamba2Bwd evolution（进化基线）round_1/parallel_2（node x0, open_exploration）；
同轮对照：node n1（自适应提核）同窗 A/B 1.1566x，与 X78 正交可组合；
node n7（ssm-scan workflow 分支）经证据链判定 P102/P133/P132 的 Cube/chunk 前提对该逐 token
elementwise+秩1外积+M=1/N=1 归约的算子**无对应算子**（块间状态已由 host 物化 S_all），未生效。

## 前置条件 / 边界（2026-09-24 补记：33_Mamba2Fwd round_3/parallel_1）

> ⚠️ **本卡的前置是「被归约缓冲上存在 L 长的标量 FADD 依赖链」。该前置不成立时，本卡的分组保序
> WholeReduceSum 形态没有对象，硬套是倒退。**

33_Mamba2Fwd（Mamba-2 SSD 逐 token 递推前向，纯 AIV）实测：该算子 per-token 有 4 处归约，**全部已经是
向量 `ReduceSum`**（`reduce_sum_dyn` + `Ps×NP` 的 Mul→ReduceSum 形态），不存在
`for(i<L) s += buf.GetValue(i)` 这类 L 长标量累加链。因此：
- 本卡的「按 64 元素分组 + 位掩码 WholeReduceSum」**无对应算子**，未采纳；
- 该算子真正生效的是**同名的策略目标**（标量链清零）在**另一种载体**上的实现 —— 把挂在 token 循环里的
  **门控/预处理标量链**整体外提为 token-slab 向量化（含全屏障 3→1）。该形态已沉淀为 **X97**。

**判定顺序（推荐）**：
1. 先 grep 是否存在 L 长的**标量累加/标量读**链（`GetValue` 出现在归约体内、`for` 包裹 `+=`）→ 命中用**本卡**；
2. 若归约已全向量化、但 per-token 仍有**门控/预处理标量壳**（`PipeBarrier<PIPE_ALL>` 多道 + dt/门控链走标量）
   → 用 **X97**（门控链整片外提 + 全屏障 N→1 + 内层 pass 数收敛）；
3. 两者可组合：归约链长的算子先本卡，再叠 X97。

**另一条独立边界**（同算子实测，与 X78 的「保序」红线互补）：本卡的「归约块 DMA 合并」在实现上会抬高 UB
占用，从而**暴露下游 API 的 scratch 真实需求** —— 该算子实测 `reduce_sum_dyn` 的 `sharedTmpBuffer`
实际需约 `Ps*NP*4` 字节（父变体硬编码 `TMP_UB_BYTES=16384` 只够 `Ps<=64`，超写部分此前静默落在 UB
末尾空闲区）。详见 failure-pattern **f40**。合并不等于免费，先算 UB 账。

**来源**：33_Mamba2Fwd evolution（进化基线内核模式）round_3/parallel_1（node n3_s1_s1）；
两个变体（n3_s1_s1 / x0_x1_x1）**各自独立** root-cause 出上述 scratch 越界，互为旁证。
