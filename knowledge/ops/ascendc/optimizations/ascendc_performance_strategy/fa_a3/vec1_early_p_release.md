---
type: Optimization
title: Vec1 软状态早释放与 P 数据写完成同步
description: 前移 Vec1 的软状态释放信号，P 数据仍以 MTE3 写完成事件为 ready；禁止用 PRELAUNCH 间隙替代同步。
tags:
- task.optimization
- topic.attention
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/06-vec1-early-p-release.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# Vec1 软状态早释放与 P 数据写完成同步

## 概述

在 PRELAUNCH=2 两级分块的目标 attention 算子（FA/GQA/MQA）AscendC kernel 中，AIC 可能有很高比例的时间在等待 Vec1 的 P-ready 信号。原策略曾尝试把 P-ready 信号前移到 MTE3 写 P 之前，用 PRELAUNCH=2 的时间间隙覆盖写回；但该间隙只是时序经验，不是同步保证，会让 AIC 读到半写 P，形成数据竞争。本卡修正为：**只前移软状态（max/sum/exp）的释放信号；P 数据的 ready 必须在 MTE3 写回完成后发送，或在消费前另等写完成事件。**

> 本卡相对源策略修正了同步条件：源策略的“MTE3 写 P 前发 P_READY”不应直接照搬；P 数据的 ready 必须以写完成事件为准。

## 背景

Profiler 分析通常表现为：
- AIC 等待 P-ready 信号的时间占 AIC 总时间的比例高（明显 stall）
- 当前实现：Vec1 在 SoftmaxFlashV2 完成 + Cast + MTE3 P 写回 全部完成后才发送 P-ready
- 流水线重叠是当前 kernel 的主导瓶颈

## 核心策略

### 1. 拆分两个信号，不要混用

- `SOFTMAX_READY`：SoftmaxFlashV2 + softmax state UB store 完成后立即发送，供依赖 softmax state 的 Vec2/后续阶段使用。
- `P_READY`：Cast + MTE3 写 P 完成后发送，供 AIC 的 MTE2 读取 P 使用。

如果现有代码只用一个 P-ready 信号同时承担两种语义，则**不得**把它前移到 MTE3 之前；应先拆成两个信号。

### 2. PRELAUNCH 间隙不是同步保证

PRELAUNCH=2（RING_SLOTS=3）意味着 AIC 在 step t+2 才 MTE2 读取 P，但这是调度/时序经验，不是硬件可见性保证。AIC 仍可能在 MTE3 未完成时被调度到，读到部分写入的 P。只有在以下任一条件下才能提前：

- AIC 在 MTE2 读取前显式等待一个由 MTE3 写完成事件驱动的 `P_WRITE_DONE` 信号；
- 或 P 按块拆分，每块 MTE3 写完成后发送该块的 `P_READY`，AIC 按块消费（此时信号与写完成一一对应）。

### 3. 推荐改动

- 将 `SetSignal<...>` 拆成软状态 ready 和 P 数据 ready 两处；软状态 ready 可前移，P 数据 ready 保持在 Cast+MTE3 之后。
- 若必须减少 AIC 等待：把 P 分块，逐块 `MTE3 write → P_READY(chunk)`，AIC 按块 `WaitSignal → MTE2 read`；不要用一个整块 P_READY 覆盖未完成的写。
- 保留同步回退路径：无法增加写完成事件时，恢复原流程（MTE3 完成后发 P_READY）。

## 实现要点

1. **识别信号语义**：在 kernel 的 Vec1 处理循环中确认 `SetSignal<PIPE_OUT, SIG_MODE_ALL>` 当前只承担 P 数据 ready，还是同时承担软状态 ready。
2. **拆分信号**：新增软状态 ready（可在 SoftmaxFlashV2 + state store 后发送）；P 数据 ready 保持在 Cast + MTE3 之后，或改为按块写完成事件。
3. **保持 EnQue/DeQue 顺序**：TQue 管理的 P buffer 的 EnQue → DeQue 流程不变，只调整信号语义和发送点。
4. **增加可见性验证**：profiler 中逐 tile 核对 AIC MTE2 开始时间 > Vec1 MTE3 完成时间；若无法满足，回退整块同步流程。

## 正确性红线

1. **P_READY 必须由写完成事件触发**：禁止在 Cast/MTE3 写 P 之前发送 AIC 消费的 P_READY。
2. **PRELAUNCH 间隙只能用于性能分析，不能用于正确性论证**；profiler 中“AIC MTE2 开始晚于 Vec1 MTE3 完成”只是观测，不是保证。
3. **软状态 ready 与 P 数据 ready 分离**：软状态 ready 前移不得被 AIC 误当成 P 数据 ready。
4. **分块 P_READY 必须按块配对**：每块写完成一次、信号一次、消费一次；不得漏发或合并到未完成块。
5. **验证**：每个 tile 记录 AIC MTE2 开始时间与 Vec1 MTE3 完成时间，必须满足 `MTE2_start > MTE3_done`；并做多轮数据竞争压力测试。

## 风险分析

- **数据一致性风险**：如果 AIC 在 MTE3 未完成时读取 P，会读到部分写入的数据。缓解不是“PRELAUNCH 间隙通常足够”，而是增加写完成事件或分块信号。
- **性能风险**：软状态 ready 前移可能收益有限；如果 AIC 仍需等 `P_WRITE_DONE`，AIC stall 不会因整块 P-ready 前移而下降。应实测确认收益来源。
- **PRELAUNCH=3 fallback**：增大间隙只能降低竞争概率，不能替代同步；不得作为正确性保证。

## 预期收益

- 软状态 ready 前移可缩短 Vec2/后续阶段等待。
- AIC 侧只有在增加 `P_WRITE_DONE` 或按块 P_READY 后才可能提前；整块 P-ready 前移本身不保证 AIC stall 下降。
- 不增加 UB 压力或 GM 流量。

## 验证方法

1. **编译验证**：修改后 kernel 正常编译通过。
2. **精度验证**：全部精度测试 case 通过，并增加多轮压力测试。
3. **性能验证**：profiler 中分别观察软状态 wait 与 AIC P wait；确认收益来自合法的重叠，而不是竞争。
4. **时序安全验证**：profiler 中逐 tile 确认 AIC MTE2 开始时间 > Vec1 MTE3 完成时间；若用分块 P_READY，确认每块信号与写完成配对。

## 与已有策略的关系

- 本策略依赖的前提是 softmax state 已可在 UB 中被后续阶段安全读取；可与 `03-onchip-state-cache.md`（含其子模式 B：primitive 直写目标切片）和 `05-vec-row-chunk-coalescing.md` 组合，但早发软状态信号本身不应夹带行块大小或 UB 布局改动。
- 它优化的是 Vec1 与 AIC 之间 P 数据的 ready 语义，不替代 `07-redundant-sync-elimination-compact.md` 的核内同步删减规则。
- 若实现中同时修改 chunk sizing、queue depth、UB 布局或同步删减，应拆分成独立实验，避免把收益或风险归因到信号时机。

## 检索卡（短卡）

动作：前移 Vec1 的软状态释放信号，P 数据以 MTE3 写完成事件为 ready，必要时按块发送 P_READY。
适用：多阶段 attention 流水；需缩短软状态依赖或 AIC 等待 P 的场景。
限制：禁止用 PRELAUNCH 间隙替代同步；P_READY 必须在写完成后或按块写完成后发送；软状态 ready 与 P 数据 ready 必须分离。
范围：attention kernel 的 Vec1—AIC P 数据通路。
检索词：P-ready、SoftmaxFlashV2、MTE3、WaitSignal、写完成事件、分块信号。
机会：P-ready 当前位于 softmax、状态存储、Cast 和 MTE3 写 P 之后，且 AIC 等待时间占比高。
代价：增加信号/事件或分块管理；整块 P-ready 前移不安全，不能带来无条件的 AIC 提前。
