---
type: API
title: Cube计算(ISASI)GEMV
description: Gemv的核心功能体现为：当矩阵A的维度M取值为1时，接口会自动启用Gemv功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_key_features/GEMV.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Cube计算(ISASI)GEMV

当 Mmad 的矩阵 A 维度 M=1 时，接口自动启用 GEMV 模式，退化为 1×K 行向量与 K×N 矩阵的乘法。950 可通过 MmadParams.disableGemv=true 关闭。

约束：1×K 矩阵 A 需 512B 地址对齐，K 个数据连续存储；C 矩阵为 1×N 向量，每个 1×16 子向量在 L0C Buffer 占 1024B，有效数据仅 32B 或 64B。GEMV 模式相较于非对齐处理方式搬运数据量更少、性能更好。

<!-- cannbot:related:start -->
## 相关

- [矩阵向量乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matrix_vector_multiply.md)（`explains`）：矩阵向量乘 与《Cube计算(ISASI)GEMV》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
- [基础APIGEMV](../../cube_compute_tensor_api/mmad_compute_key_features/gemv.md)（`same_topic`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《Cube计算(ISASI)GEMV》明确提供“Gemv的核心功能体现为：当矩阵A的维度M取值为1时，接口会自动启用Gemv功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
<!-- cannbot:related:end -->
