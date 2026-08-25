---
type: API
title: DataCopyPad（UBToL1非对齐数据搬运）
description: 将 Unified Buffer 中的数据经 Matmul workspace 搬运至 L1 Buffer，并支持非对齐数据的 Padding。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopyPad_UBToL1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# DataCopyPad（UB到L1带Padding搬运）

将Unified Buffer中的数据搬运到L1 Buffer，支持在搬运过程中对数据进行Padding。用于源数据长度不满足对齐要求时自动补齐。

函数原型通过模板参数指定数据类型。参数包含dstTensor、srcTensor、dataCopyParams、padParams。约束：遵循Cube计算地址对齐约束。
