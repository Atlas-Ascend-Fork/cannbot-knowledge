---
type: API
title: ExpSub
description: 将src0与src1相减，以差值作为指数计算自然常数e的幂次，并将结果写入dst。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/ExpSub_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ExpSub

将src0与src1相减，以差值作为指数计算自然常数e的幂次，并将结果写入dst。

本接口组包含 LocalTensor, LocalTensor, Reg矢量计算API。

本接口属于 UB 矢量计算复合算术接口，组合多个基础运算。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
