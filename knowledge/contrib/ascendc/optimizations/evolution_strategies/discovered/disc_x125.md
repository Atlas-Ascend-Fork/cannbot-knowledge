---
type: Optimization
title: "X125: L2 常驻权重 GEMM 的「请求率」切分器"
description: "L2 常驻权重 GEMM 的成本由「MTE2 请求条数 × 每条请求字节」决定，而不是单纯字节数；按请求率切分可让小权重 GEMM 选到合适的 baseK 与核数。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.data_movement.data_copy
  - topic.memory
  - topic.tiling
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_l2_cache_split.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/l2_cache_split.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x125.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X125）。
>
> 原始元数据：
>
> ```yaml
> id: X125
> origin: discovered
> confidence: cross_op_verified
> op_families: [matmul, cv-mix]
> bottlenecks: [scalar_loading, tiling_imbalance, mte2_stall]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x125.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x125.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# X125: L2 常驻权重 GEMM 的「请求率」切分器

## 核心思路

小权重（可驻 L2）GEMM 的成本不是字节数，而是 **MTE2 请求条数 × 每条请求字节**。
实测单核每请求耗时：`64B≈2.5ns / 128B≈2.9ns / 512B≈6.7ns / 1KB≈13ns`
（≈1.7ns 固定 + ≈60 B/ns 流式），故同为 21.2MB 权重、不同 `baseK` 的两条路径可差 3 倍。

权重 < L2 可容纳量时成本退化为
`waves × ceil(sM/bM) × ceil(sN/bN) × ceil(K/bK) × (bM+bN)`，
而 `MultiCoreMatmulTiling` 的默认解恰在最差角：`baseN = N`、`baseK = 16~32`（64/128B 请求）、
只用 1~4 个 cube 核。目标函数应改为**每波请求行数**。

## 判据与约束

- 命中条件：`op_summary` 中 `Block Dim` 仅 1~4、`aic_mte2_ratio` 高、`mul_utilization` 低；
 且权重总量可驻 L2。
- 权重远超 L2 时不适用（那里是 HBM 字节墙，见 `weight-stream-gemm-byte-ceiling` / X124）。
- 硬约束：一核一个 base tile（瓦片内零重读）、`baseN ≥ 32`、`bM·bK` 与 `bN·bK` ≤ 半个
- **API 钳位即丢弃**：若 tiling API 把请求的 base 块改小，整条候选作废，否则成本模型自我欺骗。

## 量化（本例算子, 910B2C）

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x125.json`；引用时请结合上文适用条件与失效边界判断适用范围。

