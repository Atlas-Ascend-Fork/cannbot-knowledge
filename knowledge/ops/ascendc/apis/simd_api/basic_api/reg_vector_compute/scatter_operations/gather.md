---
type: API
title: Gather
description: 根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/scatter_operations/Gather.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Gather

该指令会根据索引值indexReg将源操作数srcReg按元素收集到目的操作数dstReg中。收集过程如下图所示

头文件："basic_api/reg_compute/kernel_reg_compute_gather_mask_intf.h"。

参数：T: 源操作数和目的操作数的数据类型，两者需保持一致。支持的数据类型请参考数据类型。；U: 索引值的数据类型，支持的数据类型请参考数据类型。；S: 目的操作数的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要手动填写。；V: 索引值的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要手动填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。；indexReg(输入): 索引值，单位：元素。 类型为RegTensor。 数据类型的位宽需要与目的操作数的位宽保持一致。indexReg中的值可以重复。 如果indexReg中索。

支持数据类型：b8、b16、b32。

约束：- 源操作数和目的操作数的数据类型需保持一致。
- 索引值和目的操作数的数据类型位宽需保持一致。

仅 Ascend 950PR/Ascend 950DT 支持。
