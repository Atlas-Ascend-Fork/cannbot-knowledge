---
type: Optimization
title: "C 面按 expert 做 512B 基址错位，避开与 B 流的 L2 set 冲突"
description: "int8 grouped GEMM + SwiGLU 融合内核里，epilogue 读 C 面与 cube 的 B 流会争 L2；按 expert 给 C 面起点加 512B 基址错位，可打散 set 冲突。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
  - topic.precision
status: draft
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/l2_cache_split.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_l2_cache_split.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/gmsq_cplane_l2_skew_910b2c.json
    role: evidence
created_at: "2026-10-30T00:00:00Z"
updated_at: "2026-10-30T00:00:00Z"
platforms:
  - a2
---
> 证据：基线/变体与逐 case 数据见 [证据包 cases/gmsq_cplane_l2_skew_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/gmsq_cplane_l2_skew_910b2c.json)。

> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。


> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 gmsq-cplane-l2-skew）。
>
> 原始元数据：
>
> ```yaml
> confidence: single_op
> op_families: [matmul, moe, quantization, cube]
> operator_type: matmul
> ```

# 本例算子：C 面按 expert 做 512B 基址错位，避开与 B 流的 L2 set 冲突

## 现象
int8 grouped GEMM + SwiGLU 融合内核里，cube 已经把 `mac+fixpipe` 串行链跑满，
但 epilogue 读 C 面的 `aiv_mte2` 与 cube 的 B 流互相挤 L2：C 面行距 16KB、B 的 ND 行距 8192B，
两者 set 映射高度重叠，C 平面被 B 流冲刷，消费侧要重新从 GM 取。

## 做法（纯 host + 一处偏移计算，零字节增量）
给每个 expert 的 C 平面起点加 `g*512B` 的基址错位（workspace 只需多 `E*512B = 4KiB`），
AIC 与 AIV 共用同一个 `planeOff_[g]` 派生函数，因此 epilogue 自动跟随。
C 面行距、段数、cube 几何、drain 结构与数值全部不变。

## 验证状态

定量结果（基线/变体、用例数、聚合口径）见证据包；正文只保留机制、判据与边界。

## 适用条件
- cube 与 epilogue 在同一 MIX kernel 内、C 面经 GM 往返（MIX 融合的 grouped GEMM 通例）；
- C 面行距与 B 的行距接近整数倍（2 的幂）时 set 冲突最重，错位收益最大；
- 错位量取 512B（= 一个 L2 sector）即可，不必更大。

## 边界
`aic_fixpipe` 本身不动（F21 的地板在 L0C 读侧，与地址无关）；本手法只救**消费侧的 L2 命中**。