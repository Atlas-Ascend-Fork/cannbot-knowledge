---
type: Optimization
title: "X163: CV 环 scalar 比近饱和：等待阻塞 vs 发射条数"
description: "aic_scalar/aiv_scalar 统计的是标量管有周期在跑，WaitFlag/CrossCoreWaitFlag 阻塞也计入忙碌；因此高 scalar 比可能是发射受限，也可能是同步等待受限，优化方向相反。用三组对照判定：依赖中性的减指令变换、加深在飞槽、破坏性合并同步对；同时看比例与时长是否一起下降。"
tags:
  - task.debugging
  - task.optimization
  - topic.architecture
status: draft
sources: []
created_at: "2026-10-29T04:50:00Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X163: CV 环 scalar 比近饱和：等待阻塞 vs 发射条数

## 核心思路
AscendC 的 `aic_scalar_ratio` / `aiv_scalar_ratio` 统计的是**标量管有周期在跑**，而 `WaitFlag` / `CrossCoreWaitFlag` 阻塞期间标量管被记为忙。因此接近饱和的标量比既可能是「发射条数受限」，也可能是「同步等待受限」——两者优化方向**完全相反**（前者要删指令，后者要改交付节奏）。先做判定，再动手。

## 三种判据（按代价从低到高）
1. **同窗口阳性对照（最省）**：做一处**只减标量指令、不改依赖**的等效变换（如把 `% RING` 取模改回绕计数器、把只读常量提到循环外）。若「比例几乎不动且时长变化很小」→ 标量管不在临界路径。
2. **深度对照**：把在飞槽数加深（例如 RING 3→4）。若比例明显下降而时长不变 → 等待周期确实离开了标量管，但**它不是墙**；墙在别处（通常是每 score 的 K/V+S/P 字节量与重叠质量）。
3. **破坏性对照**：合并同步对（例如把 `n_chunks=2` 的两对 L0B M_MTE1 wait/set 合成一对）。若明显变慢，证明「逐槽信用」是承重结构：合并后 fill 要等两条 mma 都退休，mma 又反过来等另一条 fill。

## 适用场景
- A2/910B 上的 CV 融合环（FA、MoE、matmul+vector 后处理）。
- 标量比高但 mac/vec 都明显低于饱和时，**不要**默认走「减标量指令」路线；先做判据 1。

## 实现要点
- 判据 1 的改动必须**依赖中性**：只改算术等价物（取模、常量、索引），不能改 Set/Wait 的 id、条数、成对关系。
- 每次只动一处，用 interleaved A/B（同设备同窗口、至少 2 轮交替、只差 `.so`）而不是前后两次全量。
- 结论要写进 implementation_note 的 7-metric 表：最高 pipe、是否假饱和、改动与该 pipe 变化的因果。
- 「比例降而时长不降」是一个可复用的判据：它说明该 pipe 不在临界路径，继续优化该 pipe 不会移动墙。

## 边界
- 若目标算子的标量比不高，或 mac/vec 已明显饱和，本卡的"等待阻塞"解释不适用。
- 破坏性对照只用于判定，不应保留在最终实现里。

## 验证方法
- 三组对照各自单独运行；记录比例与墙钟。
- 同窗口 A/A 噪声带；小收益必须大于噪声带。
- 用 7-metric PipeUtilization 交叉确认最高 pipe 是否变化。

## 关联
- 与 [X141](disc_x141.md)（per-iteration 恒定成本诊断）和 [X176](disc_x176.md)（scalar 高占用真假判定）互为补充。
- 与 [X157](disc_x157.md)（0x2 信用批量化）共享"逐槽信用是承重结构"的结论。

## 补充判据（跨算子复核）

- **逐行标量 `GetValue` + `PipeBarrier<PIPE_ALL>` 外提是高价值固定开销**：当每行一次 `GetValue` 并在行内插全管道 barrier 时，单次迭代的全流水 stall 可能从十余次降到 2–3 次；把 `m_i/av` 的标量读和 barrier 提到循环外，单测可 +1.6%，与 barrier 内提叠加 +3.0%。
- **反例**：不要顺手把逐行掩码应用改成整 tile `Broadcast`——广播原语的开销可能大于节省，实测回退 3.3%。只做“标量 / barrier 外提”这一层。
- 验证时把“比例下降”与“墙钟下降”分开记录；与 X97 的“门控 / 标量壳外提”配合看。
