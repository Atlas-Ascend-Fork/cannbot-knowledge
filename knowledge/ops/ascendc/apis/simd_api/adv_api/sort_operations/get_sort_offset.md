---
type: API
title: GetSortOffset
description: 根据元素位置，获取Sort数据中的对应偏移量（单位为字节）。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/GetSortOffset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetSortOffset

获取Sort接口的偏移量信息。

函数原型：uint32_t GetSortOffset(const int32_t repeatTime)

参数：repeatTime为重复次数。返回值：返回Sort偏移量。约束：无。
