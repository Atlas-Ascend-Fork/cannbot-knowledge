---
type: API
title: Prelu
description: 实现PReLU激活函数，源操作数srcReg0大于0的元素直接写入目的操作数，否则与srcReg1对应元素相乘后写入。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Prelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Prelu

该接口用于实现PReLU（Parametric ReLU）激活函数：当源操作数srcReg0中对应元素大于0时，直接将该元素写入目的操作数dstReg；否则将srcReg0与srcReg1对应元素相乘的结果写入dstReg。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_binary_intf.h"。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；U: 源操作数和目的操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg0(输入): 源操作数。 类型为RegTensor。 源操作数的数据类型需要与目的操作数保持一致。；srcReg1(输入): 源操作数。 类型为RegTensor。 源操作数的数据类型需要与目的操作数保持一致。；mask(输入): 源操作数中元素有效性的指示，详细说明请参考MaskReg。

支持数据类型：half、float。

仅 Ascend 950PR/Ascend 950DT 支持。
