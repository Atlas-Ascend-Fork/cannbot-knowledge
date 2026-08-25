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
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 基础双目算术更多样例

基础算术接口更多样例，演示通过 tensor 高维切分 mask 连续与逐比特模式实现数据非连续计算。

本接口属于 UB 矢量计算基础算术接口，操作 Unified Buffer 上的 LocalTensor 数据。

# 更多样例 - 通过tensor高维切分计算接口中的mask连续模式，实现数据非连续计算。 结果示例如下： - 通过tensor高维切分计算接口中的mask逐比特模式，实现数据非连续计算。 结果示例如下： - 通过控制tensor高维切分计算接口的Repeat Stride参数，实现数据非连续计算。 结果示例如下： - 通过控制tensor高维切分计算接口的DataBlock Stride和Repeat Stride参数，实现数据非连续计算。 结果示例如下： - 需要传入标量参数的API使用样例。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
