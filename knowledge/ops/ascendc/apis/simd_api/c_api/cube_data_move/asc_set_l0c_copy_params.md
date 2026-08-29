---
type: API
title: AscSetL0cCopyParams
description: 设置L0C搬运随路格式转换（NZ转ND）的相关配置。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_l0c_copy_params.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscSetL0cCopyParams

DataCopy从L0C Buffer搬运到Global Memory或L1 Buffer过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。

参数：nd_num(输入): ND矩阵的数量，取值范围：nd_num∈[1, 65535]。；src_nd_stride(输入): 以分形大小为单位的源步长，源相邻nz矩阵的起始地址间的偏移。  src_nd_stride∈[1, 512]，单位：fractal_size 1024B。；dst_nd_stride(输入): 目的相邻ND矩阵的起始地址间的偏移。单位为元素。   dst_nd_stride∈[1, 65535]。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL0c2Gm](asc_copy_l0c2gm/asc_copy_l0c2gm.md)（`related`）：DataCopy从L0C Buffer搬运到Global Memory或L1 Buffer过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；将矩阵计算结果从L0C Buffer搬运至GM，支持随路量化、ReLU、格式转换等能力，包含不同架构版本实现。；配置接口为 L0C 搬运的 NZ→ND 随路格式转换设置参数，asc_copy_l0c2gm 是执行同一 L0C→GM 格式转换搬运的接口族。
<!-- cannbot:related:end -->
