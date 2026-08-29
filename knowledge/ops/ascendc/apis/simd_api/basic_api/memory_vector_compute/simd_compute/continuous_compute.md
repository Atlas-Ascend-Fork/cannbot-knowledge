---
type: API
title: 连续计算（SIMD计算）
description: 连续计算API，支持Tensor前n个数据计算。针对源操作数的连续n个数据进行计算并连续写入目的操作数，解决一维Tensor的连续计算问题。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/SIMD_compute/continuous_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: [agnostic]
---

# 连续计算（SIMD计算）

连续计算API，支持Tensor前n个数据计算。针对源操作数的连续n个数据进行计算并连续写入目的操作数，解决一维Tensor的连续计算问题。

本接口属于 UB 矢量计算 SIMD 计算接口。

## 计算范围

- 源操作数与目的操作数都从各自 Tensor 的起始位置连续访问。
- 调用方通过元素个数 `n` 指定有效计算范围，不需要额外描述高维切分或 stride。
- 数据并非连续布局时，应改用支持高维切分、mask 或 stride 的接口形式，不能把 `n` 当作跨步长度。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
