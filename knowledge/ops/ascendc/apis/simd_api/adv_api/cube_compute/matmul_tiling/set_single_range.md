---
type: API
title: SetSingleRange
description: 设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetSingleRange.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetSingleRange

设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。

参数：
- maxM（输入）：设置最大的singleCoreM值，默认值为-1，表示不设置指定的singleCoreM最大值，该值由Tiling函数自行计算。
- maxN（输入）：设置最大的singleCoreN值，默认值为-1，表示不设置指定的singleCoreN最大值，该值由Tiling函数自行计算。
- maxK（输入）：设置最大的singleCoreK值，默认值为-1，表示不设置指定的singleCoreK最大值，该值由Tiling函数自行计算。
- minM（输入）：设置最小的singleCoreM值，默认值为-1，表示不设置指定的singleCoreM最小值，该值由Tiling函数自行计算。
- minN（输入）：设置最小的singleCoreN值，默认值为-1，表示不设置指定的singleCoreN最小值，该值由Tiling函数自行计算。

返回值：-1表示设置失败；0表示设置成功。
