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

- [Sort](sort.md)（`related`）：获取Sort接口处理的数据长度。；排序函数，按照数值大小进行降序排序。支持带和不带SortConfig模板参数两种原型。不带Config时执行标准降序排序；带Config时可配置排序参数。。GetSortLen 按 repeatTime 计算 Sort 处理长度，Sort 卡给出该长度所服务的降序 score/index 执行接口与临时空间合同。
<!-- cannbot:related:end -->
