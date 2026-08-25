---
type: API
title: GetSortMaxMinTmpSize
description: 在host侧获取带SortConfig模板参数的Sort接口计算所需的最大和最小临时空间大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/GetSortMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetSortMaxMinTmpSize

host侧Tiling接口，用于获取Sort接口所需的最大和最小临时空间大小。

函数原型：void GetSortMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。在minValue到maxValue范围内临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetSortLen](get_sort_len.md)（`related`）：GetSortMaxMinTmpSize 负责“在host侧获取带SortConfig模板参数的Sort接口计算所需的最大和最小临时空间大小”；GetSortLen 负责“根据元素数量，获取Sort数据的大小（单位为字节）”。
- [GetSortOffset](get_sort_offset.md)（`related`）：GetSortOffset 与《GetSortMaxMinTmpSize》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
- [GetSortTmpSize](get_sort_tmp_size.md)（`related`）：GetSortMaxMinTmpSize 负责“在host侧获取带SortConfig模板参数的Sort接口计算所需的最大和最小临时空间大小”；GetSortTmpSize 负责“获取Sort接口所需的临时空间大小”。
- [Sort](sort.md)（`related`）：Sort 支持框架申请或外部 sharedTmpBuffer 两种重载，外部缓存的合法大小由 GetSortMaxMinTmpSize 明确给出。
<!-- cannbot:related:end -->
