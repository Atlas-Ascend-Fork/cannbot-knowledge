---
type: API
title: AscLeakyrelu
description: 按元素执行Leaky ReLU操作，大于0的元素直接写入目的操作数，否则乘以标量value后写入。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_leakyrelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscLeakyrelu

该接口用于按元素执行Leaky ReLU（Leaky Rectified Linear Unit）操作：当源操作数中某元素大于0时，直接将该元素写入目的操作数；否则将该元素乘以标量值value后写入目的操作数。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscPrelu](asc_prelu.md)（`related`）：《AscPrelu》说明实现PReLU激活函数，源操作数src0大于0时直接写入dst，否则将src0与src1相乘后写入dst。；《AscLeakyrelu》说明按元素执行Leaky ReLU操作，大于0的元素直接写入目的操作数，否则乘以标量value后写入。。二者在AscPrelu和Reg/Memory Prelu共享逐元素双输入负半轴乘法，LeakyReLU则是标量斜率特例上存在可执行的直接衔接。
- [AscLeakyrelu](../../vector_compute/asc_leakyrelu.md)（`same_topic`）：Vector AscLeakyrelu 与 Reg AscLeakyrelu 执行相同负半轴乘 slope 的激活，可按 UB 与寄存器数据路径选择。
- [LeakyRelu](../../../basic_api/memory_vector_compute/basic_arithmetic/leaky_relu.md)（`same_topic`）：LeakyRelu 与《AscLeakyrelu》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [LeakyRelu](../../../basic_api/reg_vector_compute/basic_arithmetic/leaky_relu.md)（`same_topic`）：C++ Reg LeakyRelu 是同一寄存器操作的对应接口，提供直接的 C/C++ 映射。
<!-- cannbot:related:end -->
