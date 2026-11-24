---
type: Optimization
title: 单调可见边界下沉到 L1→L0 搬载级裁剪
description: 将单调可见边界判定下沉至L1→L0搬载，跳过完全不可见微块的装载。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/02-monotonic-visibility-l1-l0-load-skip.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：单调可见边界下沉到 L1→L0 搬载级裁剪

> **单一优化点：** 在任务级归约块裁剪（见 01 号）已落地的前提下，对**保留的边界块**
> 内部，按单调可见边界跳过完全不可见微块的 L1→L0 tile 搬载（LoadNzL1ToNzL0A/B）与
> 对应 MAC 累加；边界微块仍保留精确处理。即把"哪些列可见"的粒度从 s2 块（01 号）
> 下沉到 BLOCK_N=128 微块。

> **状态：未验证。** 来源：K-Search 世界模型动态生成（节点 s14c1，rating 6.0，
> 挂在 s14 下，2026-08-25 MHA run1）。生成后 run 崩溃（框架 lineage bug）未执行，
> 动态节点未持久化——本卡是唯一存档点。属 01 号采纳后的下一级正交叠加方向。

---

## 1. 优化原理

### 1.1 性能问题模式

01 号裁掉整块不可见的 s2 后缀块后，**边界块内对角线右侧仍有约半个块宽的不可见
微块**（causal 对角线斜穿 BLOCK_N 网格）：以 S=1024、s2Base=2048 的末块为例，
每个 Q 微块行组 128 行对应的可见列跨 ~128 列，块宽 2048 内平均 (2048-可见宽)/2048
比例的 BLOCK_N 微块**已被装载和累加但结果全被掩码丢弃**。MM1 的 nL0Start 循环、
K 的 L1→L0B 搬载、Mmad 都在这些微块上空转。

### 1.2 核心机制

| 层 | 现状（01 号之后） | 本策略 |
|---|---|---|
| 任务级 | 不可见 s2 块不生成 ✅ | 不变 |
| 块内微块级 | 全部装载+累加，靠 ApplyMask 丢弃 | 可见界外的 (mL0,nL0) 微块对**跳过 L1→L0 装载与 Mmad** |
| 元素级 | ApplyMask 处理边界散列 ✅ | 仅边界微块需要 |

判定式（与 01 号同一 visEnd 驱动，无新参数）：微块列区间
`[nL1Start+nL0Start, +BLOCK_N)` 整体 `> visEnd - (S_kv - S) 对应行组可见终点` 时
跳过。行组粒度取 mL0 微块内**末行**（保守并集，与 01 号同口径）。

## 2. 正确性红线

- 跳过判据必须按微块内**末行**的可见终点推导（保守并集），禁用首行。
- **cL0 累加链**：Mmad 的 `cmatrixInitVal=isFirstK` 链在跳过微块后，每 (m,n) 输出
  微块的**首个被累加的 k 微块**仍必须 init；跳过的微块不得破坏 init 语义（即
  isFirstK 的判定要从"k 序号"改为"该输出微块实际执行的第一个 k"）。
- Fixpipe 写出列宽：跳过的输出微块若整列不可见，可同时跳过 Fixpipe（需与 01 号的
  s2VisCols 列宽推导合并审计，避免双重裁剪冲突）。
- online softmax 状态不受影响（本策略只在 MM1 内部，softmax 看到的 P 布局不变——
  不可见位置本就被掩成 -2^30，softmax 输出 0；跳过累加与累加 0 等价，但需确认
  P 矩阵在 wsP 中的垃圾位不被 MM2 读到：01 号的 s2VisCols 已保证）。

## 3. 泛化条件

- **适用**：01 号已落地（块内仍有大量整微块不可见）；s2BaseSize/BLOCK_N 比值越大
  （本模板 2048/128=16 微块/块）收益面越大；S 与 Skv 同量级的 causal prefill 最佳。
- **不适用**：非因果；s2VisCols 已把块宽收到 <2×BLOCK_N 时（边界微块占比高，收益小）；
  Mmad n 维按列独立累加、无法按 (m,n) 对跳过的实现结构。

## 4. 实施步骤

1. 在 ComputeMM1 的 nL0Start 循环头加可见性判定（复用 task.s2VisCols/visEnd 派生
   的行组可见终点，mL0 微块粒度）。
2. 不可见微块对：不 AllocTensor/不 EnQue L0A/L0B、不 Mmad；同步修正 isFirstK 链。
3. （可选二段）整列不可见的输出微块跳过 Fixpipe 写出。
4. 审计 vec1 侧 ApplyMask 与 s2VisCols 的语义一致性（不应有新增假设）。

## 5. LLM 前置问题

- MM1 的 (m,n,k) 三层循环中 L0 装载与 Mmad 的配对关系？isFirstK 当前如何判定？
- 边界块内不可见微块占比（可用 visEnd-s2Start 对 128 取整估算）是否 >30%？
- 跳过微块后 queL0A/B 的深度与 AllocTensor 语义是否需要显式 Free？

## 6. 风险与回退

- 主要风险在 isFirstK/cmatrixInitVal 链：跳错了首累加微块会出现随机大数值
  （精度必炸，ktest 立即暴露）。
- L0 队列 Alloc/Free 不对称会 hang（O2 级卡死，watchdog 超时）。
- 回退旋钮：跳过判定加 `enableL0Skip` 编译期或 tiling 开关，置 0 即回 01 号行为。

## 7. 验收标准

- 精度：与 01 号基线完全一致（20/20 + 长序列 12/12，无新增误差）。
- 性能：case7/8（B4_S1024 causal）在 01 号基础上再降 ≥5%；非 causal ±2% 内。
- profiling 旁证：MM1 的 Mmad 条数下降比例 ≈ 估算的不可见微块占比。

## 检索卡（短卡）

动作：将单调可见边界判定下沉至L1→L0搬载，跳过完全不可见微块的装载。
适用：已按单调可见性裁剪外层块，且保留边界块内仍有大量整微块不可见。
限制：跳过判据须按微块末行的可见终点作保守并集推导，禁止使用首行。
范围：任务级裁剪后保留边界块的块内微块。
检索词：单调可见性、L1→L0、边界块、微块、ApplyMask、nL0Start。
机会：外层裁剪后，边界块内对角线右侧仍残留整块不可见微块。
代价：适用面随s2BaseSize/BLOCK_N比值增大。
