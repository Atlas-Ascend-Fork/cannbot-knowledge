---
type: API
title: UnPack
description: 将源操作数低半或高半部分元素以高位填0或保持符号位方式扩充位宽写入目的寄存器。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_compression/UnPack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# UnPack

头文件路径为："basic_api/reg_compute/kernel_reg_compute_pack_intf.h"。

对于无符号整型，将源操作数srcReg中低半部分或高半部分的元素以高位填0扩充位宽的方式写入dstReg。对于有符号整型，将源操作数srcReg中低半部分或高半部分的元素以保持符号位扩充位宽的方式写入dstReg。

参数：T: 目的操作数数据类型。 源操作数和目的操作数的数据类型约束参考见表 源操作数和目的操作数的数据类型对应表。；U: 源操作数数据类型。；part: 枚举类型，用于控制读取srcReg的低半部分还是高半部分。 • HighLowPart::LOWEST，低位模式，读取srcReg的低半部分。 • HighLowPart::HIGHEST，高位模式，读取srcReg的高半部分。 注：RegTraitNumTwo只支持LOWEST模式。；S: 目的操作数RegTensor类型。；V: 源操作数RegTensor类型。；dstReg: 目的操作数。 类型为RegTensor。；srcReg: 源操作数。 类型为RegTensor。

仅 Ascend 950PR/Ascend 950DT 支持。
