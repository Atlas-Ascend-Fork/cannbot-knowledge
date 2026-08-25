---
type: API
title: MrgSort
description: 将已排好序的最多4条队列合并排列成1条队列，结果按照score域由大到小排序。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/MrgSort.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# MrgSort

将已排好序的最多4条队列合并排列成1条队列，结果按score域由大到小排序。与Sort配合使用，先对多段数据分别排序，再通过MrgSort合并。

函数原型：template <typename T> __aicore__ inline void MrgSort(LocalTensor<T>& dst, const LocalTensor<T>& src, const LocalTensor<T>& tmp, const MrgSortInfo& mrgSortInfo, const int32_t repeatTime)

参数：dst为输出操作数；src为输入操作数（最多4条已排序队列）；tmp为临时缓存；mrgSortInfo含各队列长度等排序信息；repeatTime为重复次数。约束：遵循通用地址对齐约束。
