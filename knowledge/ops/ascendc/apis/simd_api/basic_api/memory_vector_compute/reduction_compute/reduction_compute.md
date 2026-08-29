---
type: API
title: 归约计算
description: Memory矢量计算归约接口索引页，汇总ReduceDataBlock、ReduceRepeat、ReducePairElem及ReduceMax/Min/Sum。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute/reduction_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: ['950', a2, a3]
---

# 归约计算

Memory 矢量归约计算接口集合，对 LocalTensor 元素进行降维归约。ReduceMax/ReduceMin/ReduceSum 为基础归约（最大/最小/求和）；ReduceDataBlock/ReduceRepeat/ReducePairElem 提供分块、重复、成对元素的归约控制。归约结果通常写入标量或较小 Tensor，使用前需确认归约轴与数据类型支持情况。
