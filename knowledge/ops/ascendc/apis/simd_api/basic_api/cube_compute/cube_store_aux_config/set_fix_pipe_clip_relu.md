---
type: API
title: SetFixPipeClipRelu
description: 在L0C Buffer到GM搬运随路量化后，设置ClipReLU操作的最大值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/SetFixPipeClipRelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2]
---

# SetFixPipeClipRelu

DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路量化后，设置 ClipReLU 操作的最大值。ClipReLU 计算公式为 min(clipReluMaxVal, srcData)。

参数：config 为 uint64_t 类型，表示 ClipReLU 的最大值 clipReluMaxVal。仅 Atlas 200I/500 A2 推理产品和 Kirin X90/9030 支持。
