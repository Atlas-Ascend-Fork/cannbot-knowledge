---
type: API
title: Fill（张量变换）
description: 将Global Memory上的数据初始化为指定值。该接口可用于对workspace地址或输出数据进行清零。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/Fill.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Fill

将Global Memory上的数据初始化为指定值，可用于对workspace地址或输出数据进行清零。

函数原型：template <typename T> __aicore__ inline void Fill(GlobalTensor<T>& gmWorkspaceAddr, const uint64_t size, const T value)

参数：gmWorkspaceAddr为Global Memory地址；size为元素个数；value为填充值。约束：遵循通用地址对齐约束。
