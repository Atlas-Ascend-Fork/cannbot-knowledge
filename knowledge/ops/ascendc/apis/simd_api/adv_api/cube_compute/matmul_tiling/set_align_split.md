---
type: API
title: SetAlignSplit
description: 多核切分时，设置singleCoreM/singleCoreN/singleCoreK的对齐值。比如设置singleCoreM的对齐值为64（单位为元素），切分出的singleCoreM为64的倍数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetAlignSplit.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetAlignSplit

多核切分时，设置singleCoreM/singleCoreN/singleCoreK的对齐值。比如设置singleCoreM的对齐值为64（单位为元素），切分出的singleCoreM为64的倍数。

参数：
- alignM（输入）：singleCoreM的对齐值。若传入-1或0，表示不设置指定的singleCoreM的对齐值，该值由Tiling函数自行计算。
- alignN（输入）：singleCoreN的对齐值。若传入-1或0，表示不设置指定的singleCoreN的对齐值，该值由Tiling函数自行计算。
- alignK（输入）：singleCoreK的对齐值。若传入-1或0，表示不设置指定的singleCoreK的对齐值，该值由Tiling函数自行计算。

返回值：-1表示设置失败； 0表示设置成功。
