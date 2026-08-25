---
type: API
title: Mull
description: 双目矢量计算接口，对前count个数据按元素相乘，结果写入dst0，溢出部分写入dst1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Mull_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Mull

双目矢量计算接口，对前count个数据按元素相乘，结果写入dst0，溢出部分写入dst1。

本接口组包含 地址对齐约束, 地址对齐约束, 连续计算, 通用地址对齐约束, 通用地址重叠约束。

本接口属于 UB 矢量计算基础算术接口，操作 Unified Buffer 上的 LocalTensor 数据。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
