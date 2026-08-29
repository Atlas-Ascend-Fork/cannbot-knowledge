---
type: API
title: Pack
description: 将源操作数元素的低位部分写入目的寄存器的低半部分或高半部分，实现数据位宽压缩。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_compression/Pack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Pack

头文件路径为："basic_api/reg_compute/kernel_reg_compute_pack_intf.h"。

将源操作数srcReg中的元素选取低8位（对于b16类型）、低16位（对于b32类型）、低32位（对于b64类型）写入dstReg的低半部分或高半部分。

参数：T: 目的操作数数据类型。 源操作数和目的操作数的数据类型约束参考见表 源操作数和目的操作数的数据类型对应表。；U: 源操作数数据类型。；part: 枚举类型，用于控制写入dstReg的低半部分还是高半部分。 • HighLowPart::LOWEST，低位模式，写入dstReg的低半部分。 • HighLowPart::HIGHEST，高位模式，写入dstReg的高半部分。 注：RegTraitNumTwo只支持LOWEST模式。；S: 目的操作数RegTensor类型，由编译器自动推导，用户不需要填写。；V: 源操作数RegTensor类型，由编译器自动推导，用户不需要填写。；dstReg: 目的操作数。 类型为RegTensor。；srcReg: 源操作数。 类型为RegTensor。

仅 Ascend 950PR/Ascend 950DT 支持。
