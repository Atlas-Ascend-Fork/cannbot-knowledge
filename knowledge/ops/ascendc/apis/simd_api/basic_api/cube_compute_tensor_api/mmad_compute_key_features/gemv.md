---
type: API
title: 基础APIGEMV
description: GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/mmad_compute_key_features/GEMV.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# GEMV（矩阵向量乘）

GEMV是矩阵-向量乘法的特殊优化模式，当矩阵B或A的某一维度为1时启用。通过特殊的搬运和计算策略，减少不必要的数据搬运和计算开销，提升GEMV场景性能。

GEMV模式通过Mmad接口的模板参数或Tiling配置自动识别和启用。支持half/float等数据类型。

<!-- cannbot:related:start -->
## 相关

- [矩阵向量乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matrix_vector_multiply.md)（`explains`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《矩阵向量乘》明确提供“M=1的矩阵乘场景，通过配置A矩阵数据格式为VECTOR开启GEMV模式，减少搬运数据量提升性能。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [AscMmad](../../../c_api/cube_compute/asc_mmad.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《AscMmad》明确提供“Ascend C矩阵乘加（Mmad）核心计算接口，封装昇腾NPU硬件矩阵乘加能力，用于全连接层、卷积层等神经网络算子开发。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [Mmad](../mmad_compute/mmad.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《Mmad》明确提供“完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C，支持普通模式和MX模式。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [Mmad计算辅助配置接口](../mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《Mmad计算辅助配置接口》明确提供“Mmad计算辅助配置接口列表如下：”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [Mmad辅助配置说明](../../cube_compute/mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《Mmad辅助配置说明》明确提供“Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [SetMMColumnMajor/SetMMRowMajor](../../cube_compute/mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《SetMMColumnMajor/SetMMRowMajor》明确提供“控制Mmad/MmadWithSparse优先通过M/N的哪个方向。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [TCubeTiling结构体](../../../adv_api/cube_compute/matmul_tiling/t_cube_tiling_struct.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《TCubeTiling结构体》明确提供“TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [Cube计算(ISASI)GEMV](../../cube_compute/mmad_compute_key_features/gemv.md)（`same_topic`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《Cube计算(ISASI)GEMV》明确提供“Gemv的核心功能体现为：当矩阵A的维度M取值为1时，接口会自动启用Gemv功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [K方向对齐约束](../../cube_compute/mmad_compute_key_features/k_direction_alignment_constraint.md)（`same_topic`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《K方向对齐约束》明确提供“Atlas A2 训练系列产品/Atlas A2 推理系列产品/Atlas A3 训练系列产品/Atlas A3 推理系列产品，Mmad接口支持开启此特性。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [Mmad计算关键特性说明](mmad_compute_key_features.md)（`same_topic`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《Mmad计算关键特性说明》明确提供“本节介绍Mmad矩阵乘计算中的GEMV、HF32和UnitFlag等关键特性，帮助理解不同计算模式、精度模式和细粒度同步机制。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
<!-- cannbot:related:end -->
