---
type: API
title: CopyL1ToL0ScaleB
description: 通过Tensor API的Copy接口将L1 Buffer中的右矩阵缩放数据搬运到L0ScaleB Buffer，数据类型固定为fp8_e8m0_t。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/Copy_L1ToL0ScaleB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Copy（L1到L0BScale数据搬运）

通过统一Copy接口将L1 Buffer中ScaleB数据搬运到L0BScale Buffer，用于MX矩阵计算中Scale系数输入。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。

函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。
