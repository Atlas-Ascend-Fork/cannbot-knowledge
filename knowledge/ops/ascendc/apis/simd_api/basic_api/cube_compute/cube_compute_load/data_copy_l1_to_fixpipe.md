---
type: API
title: DataCopy
description: 将随路量化参数从L1 Buffer搬运到Fixpipe Buffer。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_L1ToFixpipe.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（L1到Fixpipe搬运）

将L1 Buffer中的数据搬运到Fixpipe，用于Cube计算中Fixpipe数据处理。

函数原型通过模板参数指定数据类型。参数包含dstTensor（Fixpipe目的）、srcTensor（L1源）、dataCopyParams（搬运参数）。约束：遵循Cube计算地址对齐约束。
