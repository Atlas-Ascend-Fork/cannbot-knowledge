---
type: API
title: DataCopy
description: 随路格式转换数据搬运，将数据从Global Memory搬运至L1 Buffer（TPosition为A1/B1），搬运过程中完成DN到NZ格式转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_DN2NZ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# DataCopy（GM到L1 DN2NZ格式转换）

将Global Memory中的DN格式数据搬运到L1 Buffer并转换为NZ格式。用于矩阵计算输入的随路格式转换搬入。

函数原型通过模板参数指定数据类型。参数包含dstTensor（L1目的NZ格式）、srcTensor（GM源DN格式）、dataCopyParams（搬运参数含源/目的shape等）。约束：源/目的地址需满足对齐要求；遵循Cube计算格式转换约束。
