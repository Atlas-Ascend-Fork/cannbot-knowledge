---
type: API
title: Muls
description: 双目矢量标量计算接口，将矢量tensor每个元素与标量求积。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Muls.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Muls

标量矢量计算接口，每个元素乘以标量值。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = src_i * scalarValue。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [AscMuls](../../../c_api/reg/arithmetic_compute/asc_muls_deprecated.md)（`related`）：Memory Muls 在 LocalTensor 上执行矢量标量乘法，可在不显式管理寄存器时替代废弃 C Reg 形态。
- [Exp](exp.md)（`related`）：指数类激活常先对输入缩放；Muls 是公式上游构件但不替代 Exp。
- [LeakyRelu](leaky_relu.md)（`related`）：LeakyRelu 与《Muls》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [Muls](../../reg_vector_compute/basic_arithmetic/muls.md)（`same_topic`）：Muls 的核心契约是“双目矢量标量计算接口，将矢量tensor每个元素与标量求积”；Muls 补充“根据mask对源操作数srcReg每个元素与标量scalarValue求积，将结果写入目的操作数dstReg”。
- [Muls（灵活标量位置）](muls_flexible_scalar.md)（`same_topic`）：Muls 的核心契约是“双目矢量标量计算接口，将矢量tensor每个元素与标量求积”；Muls（灵活标量位置） 补充“矢量元素与标量做乘法，支持标量在前或在后两种场景，标量可配置为LocalTensor单点元素”。
<!-- cannbot:related:end -->
