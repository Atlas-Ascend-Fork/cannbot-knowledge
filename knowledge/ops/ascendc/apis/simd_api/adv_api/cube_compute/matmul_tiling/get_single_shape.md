---
type: API
title: GetSingleShape
description: 获取计算后的singleCoreM/singleCoreN/singleCoreK。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/GetSingleShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetSingleShape

获取计算后的singleCoreM/singleCoreN/singleCoreK。

参数：
- shapeM（输出）：获取多核Tiling计算得到的singleCoreM值
- shapeN（输出）：获取多核Tiling计算得到的singleCoreN值
- shapeK（输出）：获取多核Tiling计算得到的singleCoreK值

返回值：-1表示设置失败； 0表示设置成功。
