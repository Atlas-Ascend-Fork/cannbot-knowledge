---
type: API
title: SetSplitRange
description: 设置baseM/baseN/baseK的最大值和最小值。目前Tiling暂时不支持该功能。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetSplitRange.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetSplitRange

设置baseM/baseN/baseK的最大值和最小值。目前Tiling暂时不支持该功能。

参数：
- maxBaseM（输入）：设置最大的baseM值，默认值为-1。-1表示不设置指定的baseM最大值，该值由Tiling函数自行计算。
- maxBaseN（输入）：设置最大的baseN值，默认值为-1。-1表示不设置指定的baseN最大值，该值由Tiling函数自行计算。
- maxBaseK（输入）：设置最大的baseK值，默认值为-1。-1表示不设置指定的baseK最大值，该值由Tiling函数自行计算。
- minBaseM（输入）：设置最小的baseM值，默认值为-1。-1表示不设置指定的baseM最小值，该值由Tiling函数自行计算。
- minBaseN（输入）：设置最小的baseN值，默认值为-1。-1表示不设置指定的baseN最小值，该值由Tiling函数自行计算。

返回值：-1表示设置失败；0表示设置成功。
