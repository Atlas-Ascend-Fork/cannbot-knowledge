---
type: API
title: Gatherb
description: 根据DataBlock偏移张量将输入张量按DataBlock粒度收集到结果张量中，每次迭代完成8个DataBlock的数据收集。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/scatter_gather/Gatherb_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Gatherb

根据DataBlock偏移张量将输入张量按DataBlock粒度收集到结果张量中，每次迭代完成8个DataBlock的数据收集。

本接口组包含 LocalTensor, Reg矢量计算。

本接口属于 UB 矢量计算 Scatter/Gather 接口。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
