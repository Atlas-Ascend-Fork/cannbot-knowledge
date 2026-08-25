---
type: API
title: Gather
description: 根据索引值index将源操作数按元素收集到目的操作数dstReg中，index中每个元素表示相对于baseAddr的元素位置，支持多种数据类型组合。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/Gather_discrete.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Gather

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

该指令会根据索引值index将源操作数按元素收集到目的操作数dstReg中。收集过程如图1所示

参数：T0: 目的操作数的数据类型。支持的数据类型请参考数据类型。；T1: 源操作数的数据类型。支持的数据类型请参考数据类型。；T2: 索引值的数据类型，支持的数据类型请参考数据类型。；T3: 目的操作数的RegTensor类型。例如RegTensor\，由编译器自动推导，用户不需要手动填写。；T4: 索引值的RegTensor类型，例如RegTensor\，由编译器自动推导，用户不需要手动填写。；dstReg(输出): 目的操作数，类型为RegTensor。；baseAddr(输入): 源操作数，UB中的基地址，需要32字节对齐。；index(输入): 索引值，dstReg中的每个元素在UB中相对于baseAddr的位置，单位：元素。类型为RegTensor。index中的值可以重复。 例：baseAdd。

约束：- 位于Unified Buffer的地址必须32字节对齐。
- index索引值对应的数据必须在UB有效地址范围内。
- 当T0为b16类型，T1为b8数据类型时，目的操作数的低8位与源操作数相同，高8位自动补0。例如源操作数T1数据类型为int8_t
    40=0b00101000 -> 0b0000000000101000，扩充至16位后等于40；

    -40=0b11011000 -> 0b0000000011011000，扩充至16位后等于216。

- 当源操作数数据类型T1为B64时，T0、T1、T2、T3、T4只支持以下组合
    | T0 | T1 | T2 | T3（自动推导） | T4（自动推导） | 备注 |

仅 Ascend 950PR/Ascend 950DT 支持。
