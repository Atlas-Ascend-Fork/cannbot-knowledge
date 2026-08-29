---
type: API
title: 基础双目算术更多样例
description: 基础算术接口更多样例，演示通过 tensor 高维切分 mask 连续与逐比特模式实现数据非连续计算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/more_examples.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: ['950']
---

# 基础双目算术更多样例

基础算术接口更多样例，演示通过 tensor 高维切分 mask 连续与逐比特模式实现数据非连续计算。

本接口属于 UB 矢量计算基础算术接口，操作 Unified Buffer 上的 LocalTensor 数据。

## 样例覆盖

- 使用 Tensor 高维切分接口的 mask 连续模式处理非连续数据。
- 使用 mask 逐比特模式选择离散元素。
- 通过 Repeat Stride 控制相邻 repeat 的地址跨度。
- 组合 DataBlock Stride 与 Repeat Stride 描述块内和块间跨度。
- 调用需要额外标量操作数的基础双目算术接口。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
