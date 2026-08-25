---
type: API
title: Mmad计算辅助配置接口
description: Mmad计算辅助配置接口列表如下：
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/mmad_compute_aux_config/mmad_compute_aux_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Mmad计算辅助配置接口

提供 Mmad 矩阵乘计算的辅助配置接口，用于设置计算模式与精度控制。
包含 SetMMColumnMajor/SetMMRowMajor 设置矩阵主序方向，SetHF32Mode 启用或关闭 HF32 半精度浮点模式，SetHF32TransMode 设置 HF32 转置模式。
这些接口在 Mmad 计算前调用，影响后续矩阵乘的数据排布与计算精度。

<!-- cannbot:related:start -->
## 相关

- [Mmad](../mmad_compute/mmad.md)（`related`）：《Mmad》明确“完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C，支持普通模式和MX模式。”；它与《Mmad计算辅助配置接口》的“Mmad计算辅助配置接口列表如下：”在实际调用参数、数据流或结果校验上直接衔接。
- [基础APIGEMV](../mmad_compute_key_features/gemv.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《Mmad计算辅助配置接口》明确提供“Mmad计算辅助配置接口列表如下：”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [Mmad辅助配置说明](../../cube_compute/mmad_compute_aux_config/mmad_compute_aux_config.md)（`same_topic`）：《Mmad辅助配置说明》明确“Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。”；它与《Mmad计算辅助配置接口》的“Mmad计算辅助配置接口列表如下：”在实际调用参数、数据流或结果校验上直接衔接。
- [SetMMColumnMajor/SetMMRowMajor](../../cube_compute/mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md)（`same_topic`）：SetMMColumnMajor/SetMMRowMajor 与《Mmad计算辅助配置接口》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
<!-- cannbot:related:end -->
