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

<!-- cannbot:related:start -->
## 相关

- [GetSortLen](get_sort_len.md)（`related`）：GetSortTmpSize 使用同一 repeatTime 计算 Sort 所需临时空间，和 GetSortLen 分别回答数据长度与 buffer 容量。
- [GetSortMaxMinTmpSize](get_sort_max_min_tmp_size.md)（`related`）：GetSortMaxMinTmpSize 负责“在host侧获取带SortConfig模板参数的Sort接口计算所需的最大和最小临时空间大小”；GetSortTmpSize 负责“获取Sort接口所需的临时空间大小”。
- [GetSortOffset](get_sort_offset.md)（`related`）：GetSortOffset 与《GetSortTmpSize》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
<!-- cannbot:related:end -->
