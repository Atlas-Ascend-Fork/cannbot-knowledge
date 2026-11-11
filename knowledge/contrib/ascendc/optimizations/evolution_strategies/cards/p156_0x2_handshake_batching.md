---
type: Optimization
title: "P156: CV 环 0x2 配对握手批量化（按形状门控）"
description: "CV 融合环用 mode-0x2 成对事件时，若槽信用每 task 一次，少量 task/核的形状会形成配对标步墙。把信用改成每 2 task 一次：生产者在偶数 per-core task acquire、奇数 task acquire-nowait；消费者两个 sub-block 都在奇数 task set，保持成对语义。必须重推环不变式并按形状门控，大 shape 可能变慢。"
tags:
  - task.optimization
  - topic.data_movement
  - topic.architecture
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/discovered/disc_x157.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p156_0x2_handshake_batching.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/1084df8aaa86b2e7a0ca4e723b4ea4b366cd3eeb/community/ops/ascendc-evolution-strategies/references/preconditions/P156.yaml
    role: constraint
created_at: "2026-11-03T15:14:30Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
---
# P156: CV 环 0x2 配对握手批量化（按形状门控）

> 证据状态：结构化来源为对应 X 发现记录（固定 commit）；实际算子的正确性/性能验证报告尚待补充。补齐前请把本卡视为待验证晋升，不用于强结论。

> 晋升自 X157（discovered，draft）。详细发现记录见 [../discovered/disc_x157.md](../discovered/disc_x157.md)。

## 核心思想
CV 融合环的 AIC↔AIV 同步通常用 mode-0x2 的"成对"事件：AIC 每产出一块中间量，在前向方向 acquire 一个信用；AIV 两个 sub-block 都 release 才记一次。当每个核只有少量 task 时，这个配对标步的固定成本会直接成为墙。**把信用做成"每 2 个 task 一次"就能把它摊薄一半**，代价是要重推环不变式。

## 协议改法（以 AIC=生产者、AIV=消费者、信用方向 AIV→AIC 为例）
- AIC：只在**偶数 per-core task 序号**调 `ProducerAcquire`（一个信用覆盖 2 个槽），奇数 task 调 `ProducerAcquireNoWait`。
- AIV：两个 sub-block 都只在**奇数 task** 上 set（保持 0x2 的成对语义），即 release 一次覆盖 2 个槽。
- 必须用**每核本地序号**（`prodSeq_` / `consSeq_`）划分配对边界，不能用全局 task id——1D 调度器给的是连续区间，起点可能为奇数。

## 不变式（必须自己推，抄旧公式会死锁）
- 信用覆盖 q 个槽时，在飞信用总数不得超过 `floor(DEPTH/q)`（每个信用实际占用 q 个槽）。具体不变式依赖本实现对"保留/已发未用"计数的定义，必须按实际信用语义重推，不能抄旧公式。
- 奇尾 task 是"未配对的 pair-start"，需要至少一个未配对信用（`A >= 1`）。
- ring 未满的核取 `A = ceil(tasks_per_core/q)`（正好等于 acquire 次数 ⇒ 零等待）。

## 适用场景
- A2/910B 上的 CV 融合算子里**每核 task 数很少**的形状。典型是 M=1 且每核只有几个到几十个 task。
- 不适用于每核 task 很多的大形状：锁步早已被流水掩掉，批量化反而增加一个标量分支与成对开销，可能变慢。
- M 很大且每 task 已带多行的形状通常无收益。

## 关键修改点
1. **形状门控必须实测**：先统计两族 shape 的 `tasks_per_core` 分布，取空档作为阈值；不要直接用一个"看起来合理"的常数。
2. 门控条件建议写成 `mSize == small && groupRows == 1 && tasks_per_core <= T`；T 通过同窗口 A/B 扫描，太小会丢掉小 case 的收益，太大把大 case 拉回门内反而变差。
3. **噪声纪律**：这类改动的收益通常很小，判定必须用同窗口背靠背配对 + 同码 A/A 噪声带；单次全量差值不足以定论。
4. 合成 pair 的最后一个奇尾 task 要单独处理；不要假设 task 总数是偶数。
5. 改变信用频率后，所有依赖 `DEPTH` 的 host/kernel 常量与 workspace 尺寸都要同步复核。

## 常见陷阱
- 环不变式推错会直接死锁；先用小规模、可观察的 task 数验证 Set/Wait 计数。
- 若某个形状的 task 数在运行期变化（动态 shape），门控阈值必须按运行期值判断，不能只看 host 侧静态信息。

## 验证方法
- 对 q=1（原始）与 q=2（批量化）分别跑小、中、大 task 数三档。
- 检查每个核的 acquire/release 次数与 `DEPTH` 的关系。
- 同设备同窗口交错 A/B，至少两轮正反序；报告 A/A 噪声带。

## 关联策略
- 与 [X127](../discovered/disc_x127.md)（RING/PRELAUNCH 约束）和 [X140](../discovered/disc_x140.md)（M 方向合批）共同处理 CV 环 task 粒度与信用。
