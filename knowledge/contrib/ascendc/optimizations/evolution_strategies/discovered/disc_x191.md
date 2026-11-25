---
type: Optimization
title: "X191: launch 数作为显式成本维 + 按规模门控的双路径"
description: "纯 AIV 多段流水里，打满并行度往往顺带增加 launch 数；把 launch 数当作显式成本维，并按规模门控双路径，可避免小规模下 launch 开销吃掉收益。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.tiling
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/overhead_optimization.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/core_count_kernel_type.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x191.json
    role: evidence
created_at: "2026-10-29T00:00:00Z"
updated_at: "2026-10-29T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X191）。
>
> 原始元数据：
>
> ```yaml
> id: X191
> origin: discovered
> confidence: single_op
> op_families: [reduction, elementwise, attention, cv-mix]
> bottlenecks: [tiling_imbalance, undersize_transfer, no_overlap]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x191.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x191.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X191: launch 数作为显式成本维 + 按规模门控的双路径

## 核心思路

纯 AIV 多段流水里，「把每段的并行度打满」几乎总会顺带**增加 launch 数**（把一段拆成多段，
或为每个矩阵向量积分出一个 kernel）。而每个 launch 在本平台有 **≈3us** 的固定成本
（实测：`[1,1,1,1]` 这类极小 case 的 5 个 kernel 各 2~5us；小 case 总时长 33us 里 12 个 host Cast 占 17~35us）。
于是同一手法的收益在「大 C / 大 HW」与「小 C」两侧符号相反：

```
净收益 ≈ 并行度收益(任务数 → 核数) - 3us × Δlaunch
```

## 判据（先算再动手）

- 某段「单核要搬的权重/中间量」`perCore = 4*c2*C*bytes / B`（fp32 元素数 ×4B ÷ 实际有活的核数）；
 `perCore > 150KB`（≈7us 纯搬运）才值得为该段开新 launch 做切分；
- 否则该段保持 `grid=B` 的合并形态（把多个矩阵向量积写成同一 kernel 内的分支）；
- 门限的取法：用 `[1,1,1,1]`、`C=64`、`C=384` 三档小 case 实测 launch 成本，用最大的两个 case
 实测切分收益，取交叉点；参数经 kernel 入参传入，避免多份编译。

## 适用场景

纯 AIV 多段流水（通道注意力 / 极化自注意力 / 归约链 / 门控），且：
- 存在「沿归约轴切分」或「按输出行切分」的并行度修复需求（原 grid 含 `b` 或 `b*ceil(n/NB)`）；
- case 规模跨度大（既有 `C*c2` 大到单核搬不动的，也有小到 launch 成本占主导的）。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x191.json`；引用时请结合上文适用条件与失效边界判断适用范围。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。
