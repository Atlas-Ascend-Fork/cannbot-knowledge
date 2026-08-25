---
type: API
title: DeInterleave
description: 对寄存器源操作数srcReg0和srcReg1中的元素进行解交织，存入结果寄存器dstReg0和dstReg1中。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_reorder/DeInterleave.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# DeInterleave

给定源操作数寄存器srcReg0和srcReg1，将srcReg0和srcReg1中的元素解交织存入结果操作数dstReg0和dstReg1中。解交织排列方式如下图所示，其中每个方格代表一个元素

头文件："basic_api/reg_compute/kernel_reg_compute_vec_interleave_intf.h"。

参数：T: 目的操作数和源操作数的数据类型。支持的数据类型请参考数据类型。；U: 源操作数和目的操作数的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要填写。；dstReg0<br>dstReg1(输出): 目的操作数。 类型为RegTensor。；srcReg0<br>srcReg1(输入): 源操作数。 类型为RegTensor。 源操作数的数据类型需要与目的操作数保持一致。

支持数据类型：bool、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t。

约束：- srcReg0、srcReg1、dstReg0、dstReg1的数据类型需要保持一致。
- srcReg0和srcReg1可以为同一个RegTensor。
- dstReg0和dstReg1不能为同一个RegTensor。
- 允许源操作数和目的操作数为同一个RegTensor，例如DeInterleave(srcReg0, srcReg1, srcReg0, srcReg1)。
- 数据类型为b64时，仅支持RegTraitNumTwo。

仅 Ascend 950PR/Ascend 950DT 支持。
