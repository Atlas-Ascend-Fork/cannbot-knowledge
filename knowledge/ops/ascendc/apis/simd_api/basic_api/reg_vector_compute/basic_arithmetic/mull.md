---
type: API
title: Mull
description: 根据mask对源操作数srcReg0、srcReg1按元素相乘，将乘法结果的低位部分写入dstReg0，溢出（高位）部分写入dstReg1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Mull.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Mull

该接口根据mask对输入数据srcReg0、srcReg1按元素相乘操作，将乘法结果的低位部分写入dstReg0，溢出（高位）部分写入dstReg1。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_binary_intf.h"。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；U: 目的操作数的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要填写。；dstReg0(输出): 目的操作数。 类型为RegTensor。；dstReg1(输出): 目的操作数。 类型为RegTensor。；srcReg0(输入): 源操作数。 类型为RegTensor。；srcReg1(输入): 源操作数。 类型为RegTensor。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

支持数据类型：int32_t、uint32_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Mul](mul.md)（`related`）：《Mull》说明根据mask对源操作数srcReg0、srcReg1按元素相乘，将乘法结果的低位部分写入dstReg0，溢出（高位）部分写入dstReg1。；《Mul》说明根据mask对源操作数srcReg0、srcReg1按元素相乘，将结果写入目的操作数dstReg。。二者在Mull在Memory、Reg C接口中都产生双字宽乘积，普通Mul用于核对仅保留原字宽的不同结果合同上存在可执行的直接衔接。
- [AscMull](../../../c_api/reg/arithmetic_compute/asc_mull.md)（`same_topic`）：《Mull》说明根据mask对源操作数srcReg0、srcReg1按元素相乘，将乘法结果的低位部分写入dstReg0，溢出（高位）部分写入dstReg1。；《AscMull》说明根据mask对源操作数src0、src1按元素相乘，将乘法结果的低位部分写入dst0，高位（溢出）部分写入dst1。。二者在Mull在Memory、Reg C接口中都产生双字宽乘积，普通Mul用于核对仅保留原字宽的不同结果合同上存在可执行的直接衔接。
- [Mull](../../memory_vector_compute/basic_arithmetic/mull_isasi.md)（`same_topic`）：《Mull》说明根据mask对源操作数srcReg0、srcReg1按元素相乘，将乘法结果的低位部分写入dstReg0，溢出（高位）部分写入dstReg1。；《Mull》说明双目矢量计算接口，对前count个数据按元素相乘，结果写入dst0，溢出部分写入dst1。。二者在Mull在Memory、Reg C接口中都产生双字宽乘积，普通Mul用于核对仅保留原字宽的不同结果合同上存在可执行的直接衔接。
<!-- cannbot:related:end -->
