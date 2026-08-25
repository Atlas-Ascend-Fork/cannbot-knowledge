---
type: API
title: MulAddDst
description: 将两个源操作数逐元素相乘再加到目的操作数上，结果写回目的操作数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/composite_compute/MulAddDst.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# MulAddDst

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_binary_intf.h"。

该接口按元素将srcReg0与srcReg1相乘再加上dstReg，根据mask将计算结果写入dstReg。

参数：T: 操作数数据类型。；mode: MaskMergeMode枚举类型。选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；U: 目的操作数和源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。计算前作为被加数参与运算，计算后存储结果。；srcReg0(输入): 源操作数。 类型为RegTensor。数据类型需要与目的操作数保持一致。；srcReg1(输入): 源操作数。 类型为RegTensor。数据类型需要与目的操作数保持一致。；mask(输入): 源操作数元素有效性的指示，详细说明请参考MaskReg。

约束：- 本接口支持寄存器重叠。
- 本接口操作数为寄存器，不涉及地址对齐。
- 本接口不修改全局寄存器的值。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差](../../../../../runbooks/precision/muladddst_fma_golden_mul_add.md)（`exemplifies`）：Runbook 的根因正是该 Reg MulAddDst 对 src0*src1+dst 执行融合乘加、只做一次舍入；API 卡给出实际操作数和 mask 契约。
- [MulAddDst](../../memory_vector_compute/composite_compute/mul_add_dst.md)（`related`）：Reg MulAddDst 与 Memory API 都实现 dst=src0*src1+dst；前者揭示寄存器级 FMA 路径，后者在 UB Tensor 上暴露 mask/repeat 约束。
- [AscMulAdd](../../../c_api/vector_compute/asc_mul_add.md)（`same_topic`）：AscMulAdd说明执行矢量的乘加运算。
- [Axpy](axpy.md)（`same_topic`）：MulAddDst说明将两个源操作数逐元素相乘再加到目的操作数上，结果写回目的操作数。
- [MulDstAdd](mul_dst_add.md)（`same_topic`）：MulDstAdd 与《MulAddDst》的衔接是：MulDstAdd 与 MulAddDst 共享乘加写回但目标操作数位置不同；ZEROING trait 是 focal 明确允许的掩码模式，错误沿用累加式 mask 会改变写回结果。
<!-- cannbot:related:end -->
