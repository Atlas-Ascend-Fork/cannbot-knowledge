---
type: API
title: AscPrelu
description: 实现PReLU激活函数，源操作数src0大于0时直接写入dst，否则将src0与src1相乘后写入dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_prelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscPrelu

该接口用于实现PReLU（Parametric ReLU）激活函数：源操作数src0大于0的情况下直接将src0写入目的操作数dst，否则将src0 * src1的结果写入dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscLeakyrelu](asc_leakyrelu.md)（`related`）：《AscPrelu》说明实现PReLU激活函数，源操作数src0大于0时直接写入dst，否则将src0与src1相乘后写入dst。；《AscLeakyrelu》说明按元素执行Leaky ReLU操作，大于0的元素直接写入目的操作数，否则乘以标量value后写入。。二者在AscPrelu和Reg/Memory Prelu共享逐元素双输入负半轴乘法，LeakyReLU则是标量斜率特例上存在可执行的直接衔接。
- [Prelu](../../../basic_api/reg_vector_compute/basic_arithmetic/prelu.md)（`related`）：AscPrelu 与 Reg Tensor Prelu 都以逐 lane 的 src0 正负分支选择 src0 或 src0*src1；前者是 C 指针/寄存器接口，后者是 C++ RegTensor 接口。
- [基础算术](arithmetic_compute.md)（`related`）：《AscPrelu》说明实现PReLU激活函数，源操作数src0大于0时直接写入dst，否则将src0与src1相乘后写入dst。；《基础算术》说明寄存器侧基础算术类接口汇总，提供abs、add、sub、mul、div、exp、ln、sqrt、relu等逐元素矢量计算能力。。二者在AscPrelu和Reg/Memory Prelu共享逐元素双输入负半轴乘法，LeakyReLU则是标量斜率特例上存在可执行的直接衔接。
- [Prelu](../../../basic_api/memory_vector_compute/basic_arithmetic/prelu_isasi.md)（`same_topic`）：《AscPrelu》说明实现PReLU激活函数，源操作数src0大于0时直接写入dst，否则将src0与src1相乘后写入dst。；《Prelu》说明双目矢量计算接口，src0非负时直接输出，否则输出src0与src1的乘积。。二者在AscPrelu和Reg/Memory Prelu共享逐元素双输入负半轴乘法，LeakyReLU则是标量斜率特例上存在可执行的直接衔接。
<!-- cannbot:related:end -->
