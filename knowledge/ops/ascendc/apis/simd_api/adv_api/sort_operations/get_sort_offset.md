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

<!-- cannbot:related:start -->
## 相关

- [Concat（排序操作）](concat.md)（`related`）：GetSortOffset 与《Concat（排序操作）》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
- [Extract（排序操作）](extract.md)（`related`）：GetSortOffset 与《Extract（排序操作）》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
- [GetSortLen](get_sort_len.md)（`related`）：GetSortOffset 与《GetSortLen》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
- [GetSortMaxMinTmpSize](get_sort_max_min_tmp_size.md)（`related`）：GetSortOffset 与《GetSortMaxMinTmpSize》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
- [GetSortTmpSize](get_sort_tmp_size.md)（`related`）：GetSortOffset 与《GetSortTmpSize》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
- [MrgSort](mrg_sort.md)（`related`）：GetSortOffset 与《MrgSort》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
- [Sort](sort.md)（`related`）：GetSortOffset 与《Sort》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
<!-- cannbot:related:end -->
