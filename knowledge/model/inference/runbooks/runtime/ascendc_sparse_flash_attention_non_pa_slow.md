---
type: Runbook
title: ascendc SparseFlashAttention 非 PA(无 block table)decode 路由到未优化模板、慢于 tilelang
description: ascendc SparseFlashAttention 非 PA(无 block table)decode 路由到未优化模板、慢于 tilelang。用 ascendc 实现的 SparseFlashAttention 算子在 decode 场景 msprof 实测明显慢于 tilelang 实现，且慢得不合理（同 shape、精度对齐下 ascendc ≈ 2.4ms、tilelang ≈ 915us，tilelang 约 2.6x 快，910B3）。据此误判「ascendc 弱于 tilelang」。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/14
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# ascendc SparseFlashAttention 非 PA(无 block table)decode 路由到未优化模板、慢于 tilelang

## 信号（报错 / 现象）
- 用 [ascendc](../../concepts/frameworks/ascendc.md) 实现的 [SparseFlashAttention](../../concepts/kernels/sparse_flash_attention.md) 算子在 decode 场景 msprof 实测明显慢于 [tilelang](../../concepts/frameworks/tilelang.md) 实现，且慢得不合理（同 shape、精度对齐下 ascendc ≈ 2.4ms、tilelang ≈ 915us，tilelang 约 2.6x 快，910B3）。据此误判「ascendc 弱于 tilelang」。

## 触发条件
- decode（`actual seq lengths query = 1` 且 `kv = 8192`：单 query token、长 KV）且 **`block table = none` → 非 PA（非 Paged Attention）场景**。
- 观测输入（ascendc 侧）：query `[4,1,128,512]`、key/value `[4,8192,1,512]`、sparse indices `[4,1,1,2048]`、layout `BSND`、sparse mode `3`、sparse block size `1`、block table `none`。msprof 记录 ascendc ≈ 2407–2424us、tilelang ≈ 915us。

## 根因
- 该非 PA 场景在 ascendc `SparseFlashAttention` 中会**路由到未优化的模板**，故性能差。ascendc 的优化实现面向 **PA（Paged Attention）** 场景——同 shape 输入在 PA 场景实测约 106us（维护者披露、单点、无独立复测）。
- 设计取舍（维护者说明）：本算子重点支持 PA 场景（更贴近外部使用、可直接适配 vLLM / [SGLang](../../concepts/frameworks/sglang.md)）；非 PA 当前暂无明确使用场景，为未优化模板，后续跟进（roadmap，非现状）。

## 修法 / 规避
- 使用 ascendc `SparseFlashAttention` 时走 **PA 路径**（提供 block table、PA 布局）命中优化模板。
- 非 PA 路径当前是未优化模板，其耗时不代表算子上限——**不要据非 PA 实测判定 ascendc 弱于 tilelang**，也不要据非 PA 数字做算子选型。
- 同 shape 对比（供预期）：PA 场景 ascendc ≈ 106us；非 PA 场景 ascendc ≈ 2407–2424us、tilelang ≈ 915us。

## 边界
- 限本仓 ascendc `SparseFlashAttention` 的 PA vs 非 PA 分支路由，不外推到其它 ascendc 算子或整个昇腾栈；106us 为单点、不写单调律；「优化后达 PA 同性能」仅 roadmap、非事实。

## Evidence
- `维护者确认`：确认「非 PA 场景在 ascendc 中路由到未优化模板」+ PA 同 shape 实测 106us + 「重点支持 PA、非 PA 暂无明确场景」。
- `reporter 一手 msprof`：scenario 截图确认 block table = none（非 PA）与全部输入 shape；results 截图确认 ascendc ≈ 2407/2424us、tilelang ≈ 915us。
- 溯源下探：[cann-recipes-infer-issue-14-question-tilelang-ascendc](https://gitcode.com/cann/cann-recipes-infer/issues/14)

<!-- cannbot:related:start -->
## 相关

- [SparseFlashAttention A2/A3 ACLNN 算子知识](../../../../ops/ascendc/operators/aclnn/transformer/attention/sparse_flash_attention.md)（`related`）：该非 PA 场景在 ascendc `SparseFlashAttention` 中会**路由到未优化的模板**，故性能差；R-001 C 连续 KV；R-002 C PageAttention；R-003 V 连续 KV；R-004 V PageAttention。运行手册定位连续 KV 与 PageAttention 的性能分叉，算子卡给出四条 Host 可达 Route，支持继续核对该分叉的 Tiling 与 Device 实现。
- [同一算子有 AscendC / pyPTO / TileLang 多后端实现时的选型 — 当前阶段优先 AscendC](../../optimizations/experience/rules/op_backend_selection_ascendc_pypto_tilelang.md)（`related`）：非 PA 路径当前是未优化模板，其耗时不代表算子上限——**不要据非 PA 实测判定 ascendc 弱于 tilelang**；真要在具体 workload 上定选型，仍应对目标算子实测三后端时延后再定。前者给出 SparseFlashAttention 非 PA 路径的反例边界，后者要求按目标 workload 实测；二者把默认后端先验收敛为可复核的具体选型流程。
- [昇腾性能测量失真陷阱：不代表真实访存的测量输入·折算前被截断的度量口径](../../optimizations/experience/anti_patterns/perf_measurement_distortion_input_and_metric.md)（`related`）：稀疏索引（`sparse_indices`）必须用「在真实 KV 长度范围内、无放回采样的互异块索引」生成；观测输入（ascendc 侧）：query `［4,1,128,512］`、key/value `［4,8192,1,512］`、sparse indices `［4,1,1,2048］`、layout `BSND`、sparse mode `3`、sparse block size `1`、block table `none`。前者规定稀疏 SFA 性能输入的代表性，后者给出非 PA 慢路径比较的具体 shape；复核该性能结论时必须把 sparse indices 的生成分布纳入验证。
<!-- cannbot:related:end -->
