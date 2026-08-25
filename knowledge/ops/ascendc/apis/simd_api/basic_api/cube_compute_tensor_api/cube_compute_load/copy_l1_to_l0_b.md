---
type: API
title: CopyL1ToL0B
description: 通过Tensor API的Copy接口将L1 Buffer中的右矩阵数据搬运到L0B Buffer，支持非转置和转置搬运。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/Copy_L1ToL0B.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Copy（L1到L0B Buffer数据搬运）

通过统一Copy接口将L1 Buffer数据搬运到L0B Buffer，用于矩阵计算右矩阵B输入。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。

支持场景：连续数据搬入、随路格式转换（L1的NZ/ZN格式到L0B的Fractal格式）、Batch多矩阵搬入。函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。
