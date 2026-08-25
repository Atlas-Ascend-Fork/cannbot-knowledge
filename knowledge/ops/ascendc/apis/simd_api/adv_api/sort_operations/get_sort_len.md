---
type: API
title: GetSortLen
description: 根据元素数量，获取Sort数据的大小（单位为字节）。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/GetSortLen.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetSortLen

获取Sort接口处理的数据长度。

函数原型：uint32_t GetSortLen(const int32_t repeatTime)

参数：repeatTime为重复次数。返回值：返回Sort处理的数据长度。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Extract（排序操作）](extract.md)（`related`）：有效排序长度决定 Extract 范围。
- [GetSortMaxMinTmpSize](get_sort_max_min_tmp_size.md)（`related`）：GetSortMaxMinTmpSize 负责“在host侧获取带SortConfig模板参数的Sort接口计算所需的最大和最小临时空间大小”；GetSortLen 负责“根据元素数量，获取Sort数据的大小（单位为字节）”。
- [GetSortOffset](get_sort_offset.md)（`related`）：GetSortOffset 与《GetSortLen》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
- [GetSortTmpSize](get_sort_tmp_size.md)（`related`）：GetSortTmpSize 使用同一 repeatTime 计算 Sort 所需临时空间，和 GetSortLen 分别回答数据长度与 buffer 容量。
<!-- cannbot:related:end -->
