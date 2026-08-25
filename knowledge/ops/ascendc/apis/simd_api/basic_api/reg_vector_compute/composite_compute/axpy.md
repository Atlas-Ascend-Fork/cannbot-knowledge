---
type: API
title: Axpy
description: 对标量与源操作数执行乘加操作，将标量乘积加到目的操作数上。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/composite_compute/Axpy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Axpy

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_ternary_scalar_intf.h"。

该接口根据mask对dstReg、srcReg和标量scalarValue按元素执行乘加操作，将结果写入dstReg。

参数：T: 操作数数据类型。；U: 标量源操作数的数据类型。；mode: MaskMergeMode枚举类型。选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；S: 目的操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数和源操作数。 类型为RegTensor。数据类型需要与源操作数保持一致。；srcReg(输入): 源操作数。 类型为RegTensor。 数据类型需要与目的操作数保持一致。；scalarValue(输入): 源操作数。 类型为标量。 数据类型需要与目的操作数保持一致。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

约束：- 本接口支持寄存器重叠。
- 本接口操作数为寄存器，不涉及地址对齐。
- 本接口不修改全局寄存器的值。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscAxpy](../../../c_api/reg/compound_compute/asc_axpy.md)（`same_topic`）：AscAxpy 与《Axpy》的衔接是：AscAxpy 的 C Vector、基础及高阶 Axpy 入口实现同一 alpha*x+y 数据流，差异集中在张量形态、临时空间和调度层级。
- [Axpy](../../memory_vector_compute/composite_compute/axpy.md)（`same_topic`）：Axpy说明计算向量和标量的乘积，并将乘积结果逐元素加到的输出向量上。
- [MulAddDst](mul_add_dst.md)（`same_topic`）：MulAddDst说明将两个源操作数逐元素相乘再加到目的操作数上，结果写回目的操作数。
- [MulDstAdd](mul_dst_add.md)（`same_topic`）：MulDstAdd说明将目的操作数与源操作数逐元素相乘再加另一个源操作数，结果写回目的操作数。
<!-- cannbot:related:end -->
