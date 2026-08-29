---
type: API
title: AscExpSub
description: 将src0与src1相减的差值作为e的指数计算，结果写入dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compound_compute/asc_exp_sub_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscExpSub

将src0与src1相减，差值作为e的指数计算，i为元素索引。- 当src0和src1为float类型时
- 当src0和src1为half类型时

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [ExpSub](../../../basic_api/reg_vector_compute/composite_compute/exp_sub.md)（`related`）：将src0与src1相减，差值作为e的指数计算，i为元素索引。- 当src0和src1为float类型时；srcReg0与srcReg1相减，差值作为e的指数计算，根据mask将计算结果写入dstReg。。两端执行相同的寄存器 ExpSub 复合运算，候选卡提供非 deprecated 的 RegTensor 参数、layout 与 mask 合同。
<!-- cannbot:related:end -->
