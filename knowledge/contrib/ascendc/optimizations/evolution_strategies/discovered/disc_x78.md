---
type: Optimization
title: "逐 token 串行 scan 的标量归约链清零（Scalar-Free Reduction：分组 WholeReduceSum 保序归约 + 归约块 DMA 合并 + 去 per-task 全屏障）"
description: "在逐 token 串行 scan（每 token 沿状态维做若干次归约）的向量核里，最贵的往往不是向量体，而是挂在 epilogue/token 循环里的标量归约链：`for (i < L) s += buf.GetValue(i);`。可用分组 WholeReduceSum 保序归约、归约块 DMA 合并与去 per-task 全屏障三步消除。"
tags:
  - task.optimization
  - topic.compute.reduction
  - topic.implementation.synchronization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X78: 逐 token 串行 scan 的标量归约链清零

## 核心思路

在**逐 token 串行 scan**（每 token 沿状态维做若干次归约）的向量核里，最贵的往往不是向量体，而是
挂在 epilogue/token 循环里的**标量归约链**：`for (i < L) s += buf.GetValue(i);` 形态。
它不是「L 条独立 load」，而是一条 **L 长、不可并行的标量 FADD 依赖链**；
当 L 接近归约维长度且每 token 多次调用时，这条链的长度可与整个 token 的
向量指令体同量级 —— 于是它成了全核关键路径，而 profiling 的向量占比看起来仍很健康。

X78 的做法（三步，全部不改数值语义）：

1. **标量链 → 定长分组向量归约（保持顺序）**：把连续归约缓冲按 **64 元素**切成 G = ceil(L/64) 组，
   每组一条 `WholeReduceSum<float, true>(grp, buf, /*mask 全 1*/ , G, 1, 1, /*dstStride>>3*/ 8)`
   （repeat 序 = 组升序 ⇒ 组内与组间都是**同一顺序**的逐元素累加），标量侧只剩
   `for (g < G) s += grp.GetValue(g);` 的组和读取。
   ⇒ 标量链从 L 降到 G，**结合序与逐元素实现逐位一致**（bf16/fp32 输出都不变）。
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
  折半树列归约虽更快，但会把低精度输出的误差推过阈值（结合序改变导致近零对消/舍入点变化）——
  **收益让位于精度**。
- 分组归约的 mask 用**位掩码**（`uint64_t[2]`）而非计数形式；缓冲尾部零填充到 64 倍数。
- 归约块 DMA 合并后仍要保持「原逐头顺序」，否则同样改序。
- UB 预算：分组缓冲 + 整块 DMA 缓冲需要额外 UB，先按归约维/并行维上限（128）算最坏情形。

## 前置条件 / 边界

> ⚠️ **本策略的前置是「被归约缓冲上存在 L 长的标量 FADD 依赖链」。该前置不成立时，本策略的分组保序
> WholeReduceSum 形态没有对象，硬套是倒退。**

若算子的 per-token 归约已经全部是向量 `ReduceSum`（如 `Mul→ReduceSum` 形态），不存在
`for(i<L) s += buf.GetValue(i)` 这类 L 长标量累加链，则本策略的「按 64 元素分组 + 位掩码
WholeReduceSum」**无对应算子**，不应采纳。此时真正对应的是**同名的策略目标**（标量链清零）
在另一种载体上的实现 —— 把挂在 token 循环里的**门控/预处理标量链**整体外提为 token-slab
向量化（含全屏障削减），该形态见 X97。

**判定顺序（推荐）**：
1. 先 grep 是否存在 L 长的**标量累加/标量读**链（`GetValue` 出现在归约体内、`for` 包裹 `+=`）→ 命中用**本策略**；
2. 若归约已全向量化、但 per-token 仍有**门控/预处理标量壳**（`PipeBarrier<PIPE_ALL>` 多道 +
   门控/预处理链走标量）→ 用 **X97**（门控链整片外提 + 全屏障 N→1 + 内层 pass 数收敛）；
3. 两者可组合：归约链长的算子先本策略，再叠 X97。

**另一条独立边界**：本策略的「归约块 DMA 合并」在实现上会抬高 UB
占用，从而**暴露下游 API 的 scratch 真实需求** —— 某些动态归约 API 的 `sharedTmpBuffer`
实际需约 `Ps*NP*4` 字节；父实现若硬编码较小的 `TMP_UB_BYTES`，超写部分会静默落在 UB
末尾空闲区。合并不等于免费，先算 UB 账。

## 验证方法
- **性能**：在目标设备上对父变体与变体做同一时间窗口的 A/B（正反序至少两轮），
  以绝对时延和配对差值判断，不用跨窗口比值。
- **精度**：跑全量精度用例，逐元素对比参考实现；bf16/fp16 输出必须与保序实现逐 bit 一致，
  不能只检查「恰好过阈值」。
- **容量**：审计 UB 预算（分组缓冲、整块 DMA 缓冲、`sharedTmpBuffer` 的 `Ps*NP*4` 需求），
  确认无越界或静默覆写。

## 补充判据（跨算子复核）

- **高级归约降级为 level-0**：带 work-buffer 的 `ReduceSum/ReduceMax<Pattern::Reduce::AR|RA>` 内部多趟、需 host 预留 tmp、且平台实测后必须接 `PIPE_ALL`。热循环里可换成：普通 `Add` 沿归约轴折半到 ≤64 元素（`BinaryRepeatParams` 规整），再 `WholeReduceSum/BlockReduceSum` 出最终值；随附的 `PIPE_ALL` 一并删除。
- **槽位密度**：折半窗口取 64 元素子块时密度 100%（每 repeat 读 64 源元素产 32 有用项），对比 64 元素窗口的 50%。
- **实测**：某 paged MLA decode 的 rope/nope/PV 三处高级归约改折半 Add + Whole/BlockReduceSum，删 3 道 PIPE_ALL，**1.176x**；PV 64 次逐行标量 Add 改整块 ReduceSum RA 列归约 1.25x 独立/1.18x 叠加；某 CV 卷积 K3 内层 C 次标量 dot 改 level-0 Mul(src0RepStride=0)+WholeReduceSum，+3.9% 端到端。
- **反例/边界**：静态削减 ≠ 墙钟收益——迭代次数降 2.64x（屏障 206136→78115）只兑现 +0.58%；先把站点账（该站点占总时间比例）算清，再决定是否动它。一次性/初始化路径的低频归约不值得换。
