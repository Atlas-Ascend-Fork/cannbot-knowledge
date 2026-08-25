---
type: API
title: CopyGmToL1
description: 通过Tensor API的Copy接口将Global Memory数据搬运到L1 Buffer，支持随路格式转换和Batch多矩阵搬入。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/Copy_GMToL1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Copy（GM到L1 Buffer数据搬运）

通过统一Copy接口将Global Memory数据搬运到L1 Buffer，用于矩阵计算输入搬入。搬运参数由Tensor Layout自动推导，用户无需额外传入搬运参数。仅Ascend 950PR/950DT支持。试验接口，后续可能调整。

支持场景：连续数据搬入（格式不变）、高维切分搬入（多段搬运）、随路格式转换搬入（ND/DN到NZ/ZN等）、Batch多矩阵搬入（支持ND2ND/ND2NZ/DN2NZ等多种格式转换）、Scale数据搬入（MX矩阵计算）、卷积特征图搬入（NC1HWC0格式转换）。

函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型，搬运块数和长度由Layout推导。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。
