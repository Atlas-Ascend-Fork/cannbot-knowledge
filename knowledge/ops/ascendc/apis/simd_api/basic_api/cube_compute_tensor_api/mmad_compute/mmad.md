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
