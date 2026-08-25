---
type: API
title: Select
description: 根据mask比特位值从两个源操作数中选取元素，比特位为1选srcReg0，为0选srcReg1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/compare_and_select/Select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Select

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_cmpsel_intf.h"。

给定两个源操作数srcReg0和srcReg1，根据mask的比特位值选取元素，得到目的操作数dstReg。当mask的比特位是1时，从srcReg0中选取对应位置的数，比特位是0时从srcReg1选取对应位置的数。

参数：T: 操作数数据类型。；U: 源操作数和目的操作数的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg0、srcReg1(输入): 源操作数。 类型为RegTensor。 两个源操作数的数据类型需要与目的操作数保持一致。；mask(输入): 指定选择源操作数的规则：mask的比特位是1时，选取srcReg0，比特位是0时，选取srcReg1。

支持数据类型：bool、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t。

约束：通过mask参数控制的未选中的元素保持源操作数的值而非清零。

仅 Ascend 950PR/Ascend 950DT 支持。
