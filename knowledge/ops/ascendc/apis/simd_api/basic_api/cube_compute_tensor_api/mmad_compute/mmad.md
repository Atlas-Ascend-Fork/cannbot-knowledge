---
type: API
title: Mmad
description: 完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C，支持普通模式和MX模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/mmad_compute/Mmad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Mmad

完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C。计算公式：C = A * B，带bias时C = A * B + Bias。仅Ascend 950PR/950DT支持。试验接口。流水类型：PIPE_M。

函数原型通过模板参数指定AtomType（矩阵计算类型）、AntiQuantType（反量化类型）等。接口参数包含dstTensor（L0C输出）、srcTensorL0A（左矩阵A）、srcTensorL0B（右矩阵B）、biasTable（bias输入，可选）、tiling（MmadTiling切分信息）等。

MmadTiling包含M/N/K轴切分参数、迭代次数、数据类型信息等。约束：遵循Cube计算地址对齐和数据类型约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [Mmad计算辅助配置接口](../mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：辅助配置页规定“这些接口在 Mmad 计算前调用，影响后续矩阵乘的数据排布与计算精度。”；Mmad 页说明“完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C。”，前者配置主序和 HF32 状态，后者是直接消费这些状态的计算。
- [Mmad](../../cube_compute/mmad_compute/mmad.md)（`same_topic`）：完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C；Ascend C 矩阵乘加核心接口，实现 C=A×B+C。两端均定义 L0A/L0B 输入、L0C 输出的矩阵乘加操作，分别是 950 Tensor API 与基础 API 形态。
<!-- cannbot:related:end -->
