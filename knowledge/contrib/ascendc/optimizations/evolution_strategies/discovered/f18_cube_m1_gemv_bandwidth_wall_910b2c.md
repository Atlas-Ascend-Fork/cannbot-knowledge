---
type: Optimization
title: "F18: M=1 GEMV 的 Cube 化是带宽墙，且受 A/B 同 dtype 约束"
description: "把 M=1 GEMV 改成 Cube 化会撞上带宽墙，且受 A/B 同 dtype 约束；小 M 的矩阵向量积更适合留在向量路径。"
tags:
  - task.debugging
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.tiling
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_pure_cube.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_continuous.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f18_cube_m1_gemv_bandwidth_wall_910b2c.json
    role: evidence
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 F18）。
>
> 原始元数据：
>
> ```yaml
> id: F18
> occurrences: 1
> failed_combination: [P102, P4, P1]
> op_families: [reduction, elementwise, attention, matmul]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/f18_cube_m1_gemv_bandwidth_wall_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f18_cube_m1_gemv_bandwidth_wall_910b2c.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F18: M=1 GEMV 的 Cube 化是带宽墙，且受 A/B 同 dtype 约束

## 现象
本例算子 本轮变体（节点 n9）：把 `q1[b,n] = Σ_c wq1[c]·x[b,c,n]`
从 AIV 的逐行 Axpy 改成 `KERNEL_TYPE_AIC_ONLY` 的 MatmulImpl（M=1 / K=c / N=n，per-b）。

- 硬件计数给出根因：`aic_mte2_ratio 0.748 / aic_mac_ratio 0.079`（最大 case 0.92 / 0.088）
 ⇒ **该段是 MTE2 带宽墙，MMA 几乎空闲**。所以「16 倍 M 向空转」并不是瓶颈，
 但反过来说：把 MMA 从 AIV 搬到 Cube 也只能省下 AIV 的标量壳，省不到搬运；
 已贴带宽上限。

## 第二处否证：`p = wt·x` 的 Cube 化被精度红线挡回
Cube 要求 A/B 操作数同 dtype，而 `wt = w ⊙ (wv2ᵀσ)` 是 fp32 消元产物。把它落成 bf16 后：

## Resolution
- **只在「该 GEMV 段同时是 AIV 标量壳主因、且其操作数本来就是同 dtype」时**才考虑 Cube 化 M=1 GEMV；
- 若硬件计数显示 `aic_mte2_ratio > 0.7`，说明已经在带宽墙，继续调 tiling 无意义；
- 更划算的方向是 AIV 内部的标量壳消除与 burst 加宽（见 X119 / X118）。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f18_cube_m1_gemv_bandwidth_wall_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

