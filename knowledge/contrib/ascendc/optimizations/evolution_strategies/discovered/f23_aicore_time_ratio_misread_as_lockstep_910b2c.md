---
type: Optimization
title: "F23: `aicore_time/dur ≈ aiv_time/dur ≈ 0.94` 不代表 AIC/AIV 串行——据此做跨 stage 流水是负收益"
description: "aicore_time/dur ≈ aiv_time/dur ≈ 0.94 不代表 AIC/AIV 严格串行；据此做跨 stage 流水是负收益，需要独立的重叠证据。"
tags:
  - task.debugging
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.compute.reduction
  - topic.compute.elementwise.arithmetic
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/performance_analysis/analyze_performance_data.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/performance_analysis/collect_performance_data.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f23_aicore_time_ratio_misread_as_lockstep_910b2c.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 aicore-time-ratio-misread-as-lockstep-910b2c）。
>
> 原始元数据：
>
> ```yaml
> confidence: single_op
> phenomenon: perf_regression
> severity: medium
> occurrences: 1
> failed_combination: [P16, P17]
> op_families: [matmul, cv-mix, attention]
> operator_type: matmul
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/f23_aicore_time_ratio_misread_as_lockstep_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f23_aicore_time_ratio_misread_as_lockstep_910b2c.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F: `aicore_time/dur ≈ aiv_time/dur ≈ 0.94` 不代表 AIC/AIV 串行——据此做跨 stage 流水是负收益

## 现象
MIX 内核（AIC 跑 GEMM、AIV 跑搬运算子）在 `op_summary` 里读到
`aicore_time/dur ≈ 0.946`、`aiv_time/dur ≈ 0.939`，看上去"两个引擎各占满整个 kernel 时长"，
于是推断二者被 `SyncAll` 锁成严格交替、总时长 = ΣAIC + ΣAIV，并据此设计"跨 stage 2 级流水

## 根因
两个误判：
1. **指标语义**：MIX 内核里 `SyncAll` 是**自旋等标志位**，自旋周期计入 core-active。
 真正判据是 `aicore_time + aiv_time ≈ 1.9 × dur` —— 若严格交替应 ≈1.0×dur。所以两侧**本来就在并发**，
 0.94 只反映"两边都在自旋/工作"。用单侧比值判断重叠状态是错的。
2. **成本构成**：用 `GetSystemCycle()` 在 AIV 15 点 / AIC 17 点插桩后实测——
 且一个新增 `SyncAll` 比它要藏的那段 AIV 工作还贵。

## Resolution
- 判定重叠状态请用 `aicore_time + aiv_time` 与 `dur` 的比值（≈2 表示并发，≈1 表示交替），
 不要用单侧 core-time/dur；
- 依赖链型的算子（每个 stage 都消费前一 stage 全部输出）**不要**做跨 stage 流水；
 优先做**减少会合次数**（合并无真实依赖的相邻 stage），而不是增加 pipeline 级；
- 插桩测量（`GetSystemCycle` 打点）是唯一能定位"固定开销 vs 等待 vs 真计算"的手段，
 但必须在交付前删除插桩点（release 下插桩会改变代码生成，见 F: aiv-direct-release-codegen-broken）。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f23_aicore_time_ratio_misread_as_lockstep_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

