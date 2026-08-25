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

<!-- cannbot:related:start -->
## 相关

- [AscExpSub](../../../c_api/reg/compound_compute/asc_exp_sub_deprecated.md)（`related`）：ExpSub 与《AscExpSub》的实质衔接是：Reg 与 C API 的 ExpSub 实现同一 exp(src)-scalar 复合运算，可用于接口迁移和语义核对。
- [ExpSub](../../reg_vector_compute/composite_compute/exp_sub.md)（`related`）：ExpSub 与《ExpSub》的实质衔接是：Reg 与 C API 的 ExpSub 实现同一 exp(src)-scalar 复合运算，可用于接口迁移和语义核对。
<!-- cannbot:related:end -->
