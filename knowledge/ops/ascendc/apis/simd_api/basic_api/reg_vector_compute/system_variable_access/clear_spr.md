---
type: API
title: ClearSpr
description: 对指定的特殊目的寄存器进行清零操作，通过模板参数指定目标特殊寄存器，调用后该寄存器值被置为0。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/system_variable_access/ClearSpr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# ClearSpr

头文件路径为："basic_api/reg_compute/kernel_reg_compute_gather_mask_intf.h"。

该接口用于对指定的特殊目的寄存器（SpecialPurposeReg）进行清零操作。通过模板参数spr指定目标特殊寄存器，调用后该寄存器的值被置为0，当前支持的特殊寄存器见表 SpecialPurposeReg模板参数说明。

参数：spr: 特殊寄存器，类型为SpecialPurposeReg枚举类。具体的取值请参考表 SpecialPurposeReg模板参数说明。；AR: 一个特殊的地址寄存器，通常配合SqueezeReg矢量计算API一起使用，SqueezeReg矢量计算API会存储有效元素的总字节数到AR寄存器。

约束：本接口只能在VF函数内调用，命名空间为AscendC::Reg，函数标记符为__simd_callee__。如果需要在VF外调用，命名空间为AscendC，函数标记符为__aicore__，具体

仅 Ascend 950PR/Ascend 950DT 支持。
