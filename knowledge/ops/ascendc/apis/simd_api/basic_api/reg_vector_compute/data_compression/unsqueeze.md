---
type: API
title: Unsqueeze
description: 以目的寄存器为源和目标，根据mask进行解压缩，生成前缀1计数序列。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_compression/Unsqueeze.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Unsqueeze

头文件路径为："basic_api/reg_compute/kernel_reg_compute_gather_mask_intf.h"。

以dstReg为源操作数和目的操作数，根据mask进行解压缩。解压缩方式：dstReg中第0个元素置为0，dstReg中的第i个元素等于mask中从第0个到第(i-1)个元素中1的数量。mask最高位被忽略不参与统计。
具体算法如下图所示，dstReg的首位为0，后续mask[i]对应mask值为1时，dstReg[i]的值为dstReg[i-1] + 1；mask[i]对应mask值为0时，dstReg[i]的值为dstReg[i-1]。

参数：T: 目的操作数的数据类型。；U: 目的操作数的RegTensor类型，由编译器自动推导，用户不需要填写。；dstReg(输入/输出): 源操作数和目的操作数。 类型为RegTensor。；mask(输入): mask用于提供dstReg解压缩信息。 类型为MaskReg。

支持数据类型：int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t。

仅 Ascend 950PR/Ascend 950DT 支持。
