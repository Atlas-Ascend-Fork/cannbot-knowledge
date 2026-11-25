---
type: Optimization
title: "F26: 用 `MIX_AIC_1_2` 把两段独立阶段合成一次 launch，比两个单引擎 launch 更贵"
description: "用 MIX_AIC_1_2 把两段独立的单引擎阶段合成一次 launch，往往比两个单引擎 launch 更贵：成对 AIV 启动与 barrier 开销超过省下的 launch 成本。"
tags:
  - task.debugging
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.tiling
  - topic.compute.elementwise.arithmetic
  - topic.compute.composite
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/CrossCoreSetFlag_ISASI.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/core_count_kernel_type.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f26_mix_aic_1_2_costs_more_than_two_single_engine_launches_910b2c.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 mix-aic-1-2-costs-more-than-two-single-engine-launches-910b2c）。
>
> 原始元数据：
>
> ```yaml
> confidence: cross_op_verified
> phenomenon: perf_regression
> severity: high
> occurrences: 2
> failed_combination: [P16, P17, X114, X113]
> op_families: [matmul, cv-mix, elementwise]
> operator_type: [matmul, cv-mix]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/f26_mix_aic_1_2_costs_more_than_two_single_engine_launches_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f26_mix_aic_1_2_costs_more_than_two_single_engine_launches_910b2c.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F26: 用 `MIX_AIC_1_2` 把两段独立阶段合成一次 launch，比两个单引擎 launch 更贵

## 现象

本例算子（11 段 launch，其中 5 段纯 AIV、6 段纯 AIC）上，两种"减少 launch 数"的
改法都被独立复现为**净回退**：

## 根因

1. **`MIX_AIC_1_2` 的成对 AIV 启动开销**：实测一次 MIX launch 12.1-22.8us，而它替换掉的两个
 单引擎 launch 合计只有 ~10-11us。原本 `KERNEL_TASK_TYPE_AIC_ONLY` 是不启动成对 AIV 的，
 改成 MIX 把这笔开销还了回来。
2. **barrier 也贵**：`SyncAll<false>` 实测 **3-7us/次**，大于它省下的 2.03-2.40us 一次 launch
3. **disjoint core slice 并发的代价**：把 24 个 cube 核劈给两个 GEMM，等于让每核的权重面板翻倍，
 权重流型 GEMM 直接亏。

## Resolution

- 想减少 launch 数，**只走"删掉阶段"**（数据布局上是精确恒等、或产物能在同一核内接力），
 不要走"合并阶段"。
- 判据：先确认被合并的两段各自是 AIC_ONLY 还是 AIV_ONLY；只要其中一段原本能免掉成对 AIV，
 合并就几乎必亏。
- 「launch 地板 2.03-2.40us」是硬墙：11 段的固定成本约 22-26us，对 68-176us 的微小 shape

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f26_mix_aic_1_2_costs_more_than_two_single_engine_launches_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

