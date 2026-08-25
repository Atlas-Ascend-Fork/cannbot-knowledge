---
type: API
title: Xor
description: 根据mask对两个RegTensor或MaskReg执行按位异或操作，将结果写入目的操作数，支持ZEROING模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/logical_compute/Xor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Xor

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_binary_intf.h"（对RegTensor操作）、"basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"（对MaskReg操作）。

本节介绍两种接口，分别用于对RegTensor和MaskReg进行操作
- 对RegTensor操作
  根据mask对输入数据srcReg0、srcReg1按位异或（^）操作，将结果写入dstReg。

- 对MaskReg操作
  根据mask对两个输入MaskReg数据src0、src1按位异或（^）操作，将结果写入dst。

参数：T: 操作数数据类型。；mode: MaskMergeMode枚举类型。选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；U: 目的操作数和源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg0(输入): 源操作数。 类型为RegTensor。 数据类型需要与目的操作数保持一致。；srcReg1(输入): 源操作数。 类型为RegTensor。 数据类型需要与目的操作数保持一致。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。；dst: 目的操作数。类型为MaskReg。

支持数据类型：bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、int64_t、uint64_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Xor](../../../adv_api/math_compute/xor_interface/xor.md)（`related`）：高阶 Xor 负责 LocalTensor 及临时空间管理，Reg Xor 提供寄存器 mask 下的同一逐元素按位异或，可用于实现层选型。
- [AscXor](../../../c_api/reg/logic_compute/asc_xor.md)（`same_topic`）：AscXor 与《Xor》的实质衔接是：高阶 Xor、基础 Reg Xor 和 AscXor 完成同一逐元素异或，差异在 LocalTensor/RegTensor/C Reg 入口和工作区管理。
<!-- cannbot:related:end -->
