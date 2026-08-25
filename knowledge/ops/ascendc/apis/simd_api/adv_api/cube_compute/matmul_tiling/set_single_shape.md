---
type: API
title: SetSingleShape
description: 设置Matmul单核计算的形状singleMIn，singleNIn，singleKIn，单位为元素。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetSingleShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetSingleShape

设置Matmul单核计算的形状singleMIn，singleNIn，singleKIn，单位为元素。

参数：
- singleMIn（输入）：设置的singleMIn大小，单位为元素，默认值为-1。-1表示不设置指定的singleMIn，该值由tiling函数自行计算。
- singleNIn（输入）：设置的singleNIn大小，单位为元素，默认值为-1。-1表示不设置指定的singleNIn，该值由tiling函数自行计算。
- singleKIn（输入）：设置的singleKIn大小，单位为元素，默认值为-1。-1表示不设置指定的singleKIn，该值由tiling函数自行计算。

返回值：-1表示设置失败；0表示设置成功。

约束：
- 在MxMatmul场景中，如果A与B矩阵的位置同时为GM，对singleKIn没有特殊限制，在这种情况下，若scaleA和scaleB的K方向大小（即Ceil(singleKIn, 32)）为奇数，用户需自行在scaleA和scaleB的K方向补0至偶数。
- 在MxMatmul场景中，当输入数据类型为fp4x2_e2m1_t、fp4x2_e1m2_t时，内轴必须为偶数。
