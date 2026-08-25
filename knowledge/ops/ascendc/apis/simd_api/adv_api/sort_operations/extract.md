---
type: API
title: Extract（排序操作）
description: 处理Sort的结果数据，输出排序后的value和index。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/Extract.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Extract

处理Sort的结果数据，输出排序后的value和index。

函数原型：template <typename T> __aicore__ inline void Extract(const LocalTensor<T>& dstValue, const LocalTensor<uint32_t>& dstIndex, const LocalTensor<T>& sorted, const int32_t repeatTime)

参数：dstValue输出排序后的值；dstIndex输出排序后的索引；sorted输入Sort的结果数据；repeatTime为重复次数。约束：遵循通用地址对齐约束。
