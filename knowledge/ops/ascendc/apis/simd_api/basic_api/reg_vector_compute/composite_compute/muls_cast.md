---
type: API
title: MulsCast
description: 将源操作数与标量相乘后按CAST_ROUND模式转换为half类型，结果写入目的操作数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/composite_compute/MulsCast.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# MulsCast

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_fused_intf.h"。

该接口用于将源操作数src与标量scalar相乘，再按照CAST_ROUND模式将结果转换为half类型，根据mask将计算结果写入目的操作数dst。

参数：T0: 目的操作数数据类型。；T1: 源操作数的数据类型。；T2: 标量源操作数的数据类型。；layout: RegLayout枚举类型。 支持RegLayout::ZERO、RegLayout::ONE。；T3: 目的操作数的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要填写。；T4: 源操作数的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。

约束：- 本接口不支持源操作数寄存器和目的操作数寄存器重叠，支持源操作数寄存器之间重叠。
- 本接口操作数为寄存器，不涉及地址对齐。
- 本接口不修改全局寄存器的值。
- Cast计算按照CAST_ROUND模式舍入。

仅 Ascend 950PR/Ascend 950DT 支持。
