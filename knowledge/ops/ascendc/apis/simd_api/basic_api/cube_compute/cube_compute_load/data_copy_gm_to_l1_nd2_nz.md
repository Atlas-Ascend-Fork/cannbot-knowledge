---
type: API
title: DataCopy
description: 将矩阵从Global Memory搬运至L1 Buffer，并在搬运过程中完成ND到NZ格式的转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_ND2NZ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（GM到L1 ND2NZ格式转换）

将Global Memory中的ND格式数据搬运到L1 Buffer并转换为NZ格式。用于矩阵计算输入的随路格式转换搬入。

函数原型通过模板参数指定数据类型。参数包含dstTensor（L1目的NZ格式）、srcTensor（GM源ND格式）、dataCopyParams（搬运参数含源/目的shape等）。约束：遵循Cube计算格式转换和地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2L1Nd2Nz](../../../c_api/cube_data_move/asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz.md)（`same_topic`）：将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。；将Global Memory中的ND格式数据搬运到L1 Buffer并转换为NZ格式。用于矩阵计算输入的随路格式转换搬入。。两卡在 C API 接口组与 C++ Basic API 中描述同一 GM→L1 的 ND 到 NZ 随路转换。
<!-- cannbot:related:end -->
