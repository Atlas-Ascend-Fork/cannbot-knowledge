---
type: API
title: DataCopy
description: 将矩阵从Unified Buffer搬运至L1 Buffer，支持非连续搬运和连续搬运，数据搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_UBToL1_highdim_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（UB到L1高维切分搬运）

将Unified Buffer中的高维数据按切分策略搬运到L1 Buffer，支持多段搬运。用于高维数据的分块搬入。

函数原型通过模板参数指定数据类型。参数包含dstTensor、srcTensor、dataCopyParams（含切分和步长信息）。约束：遵循Cube计算地址对齐约束。
