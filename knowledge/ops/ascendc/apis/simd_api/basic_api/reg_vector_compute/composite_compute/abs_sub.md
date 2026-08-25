---
type: API
title: AbsSub
description: 将两个源操作数逐元素相减再求绝对值，结果写入目的操作数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/composite_compute/AbsSub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AbsSub

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_fused_intf.h"。

该接口根据mask将srcReg0与srcReg1逐元素相减再求绝对值，计算结果写入dstReg。

参数：T: 目的操作数和源操作数的数据类型。；mode: MaskMergeMode枚举类型。选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；U: 目的操作数和源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg0(输入): 源操作数。 类型为RegTensor。；srcReg1(输入): 源操作数。 类型为RegTensor。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

仅 Ascend 950PR/Ascend 950DT 支持。
