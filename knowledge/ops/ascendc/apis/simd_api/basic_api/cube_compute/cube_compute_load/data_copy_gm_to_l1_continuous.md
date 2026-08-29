---
type: API
title: DataCopy
description: 将矩阵从Global Memory连续搬运至L1 Buffer（TPosition为A1/B1），数据搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（GM到L1连续搬运）

将Global Memory中的连续数据搬运到L1 Buffer，数据格式不变。用于矩阵计算输入的连续数据搬入。

函数原型通过模板参数指定数据类型。参数包含dstTensor（L1目的）、srcTensor（GM源）、dataCopyParams（搬运参数含shape/stride等）。约束：源/目的地址需满足对齐要求；遵循Cube计算地址对齐约束。
