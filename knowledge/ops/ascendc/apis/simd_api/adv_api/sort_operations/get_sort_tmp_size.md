---
type: API
title: GetSortTmpSize
description: 获取Sort接口所需的临时空间大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/GetSortTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetSortTmpSize

获取Sort接口所需的临时空间大小。

函数原型：void GetSortTmpSize(const int32_t repeatTime, uint32_t& maxValue)

参数：repeatTime为重复次数；maxValue输出所需临时空间大小。约束：无。
