---
type: API
title: GatherB
description: 根据索引值index将源操作数按DataBlock（32B）收集到目的操作数dstReg中，index仅前8个元素有效，每个元素对应一个DataBlock。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/GatherB_discrete.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# GatherB

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

该指令会根据索引值index将源操作数按DataBlock（32B）收集到目的操作数dstReg中。收集过程如图1所示
以下Python代码用于等价描述GatherB的数据选择过程。

参数：T: 目的操作数和源操作数的数据类型。支持的数据类型请参考数据类型。；U: 目的操作数的RegTensor类型。例如RegTensor\ ，由编译器自动推导，用户不需要手动填写。；S: 索引值的RegTensor类型，例如RegTensor\ ，由编译器自动推导，用户不需要手动填写。；dstReg(输出): 目的操作数，类型为RegTensor。；baseAddr(输入): 源操作数，UB中的基地址，需要32字节对齐。；index(输入): 索引值，dstReg中的每个DataBlock在UB中相对于baseAddr的位置，仅前8个元素有效。单位：字节。类型为RegTensor。索引值必须32B对齐，即一个索引值对应1个DataBlock。index中的值可以重复。例如： baseAddr: [DataBlock0, DataBlock1, DataBlock2, DataBlock3, DataBlock4, DataBlock5, DataBlock6, DataBlock7, ... , DataBlock32, ...]。 index: [0*32, 1*32, 2*32, 3*32, 4*32, 5*32, 6*32, 32*32] dstReg: [DataBlock0, DataBlock1, DataBlock2, DataBlock3, DataBlock4, DataBlock5, DataBlock6, DataBlock32]。；mask(输入): DataBlock搬运的有效指示，按b32格式解释。一个DataBlock对应4bit，仅每4bit中的最低位有效。由于index仅前8个元素有效，因此mask仅使用前8个b32元素对应的bit 0、4、8、12、16、20、24、28，分别控制dstReg中DataBlock0至DataBlock7是否更新，其余bit无效。详细说明请参考MaskReg。

支持数据类型：b8、b16、b32、b64。

约束：- 位于UB的地址必须32字节对齐。
- 源操作数和目的操作数数据类型必须相同。
- index索引值必须32字节对齐，即一个索引值对应1个DataBlock。
- index索引值对应的数据必须在UB有效地址范围内。
- RegTensor模板参数regTrait只支持RegTraitNumOne。
- index仅前8个元素有效。

仅 Ascend 950PR/Ascend 950DT 支持。
