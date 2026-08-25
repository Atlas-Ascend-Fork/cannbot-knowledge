---
type: API
title: ExpSub
description: 将两个源操作数相减的差值作为e的指数进行计算，结果写入目的操作数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/composite_compute/ExpSub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# ExpSub

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_fused_intf.h"。

srcReg0与srcReg1相减，差值作为e的指数计算，根据mask将计算结果写入dstReg。srcReg数据类型为float时
srcReg数据类型为half时

参数：T: 目的操作数数据类型。；U: 源操作数数据类型。；layout: RegLayout枚举类型。 • src类型为half类型时，支持RegLayout::ZERO、RegLayout::ONE。具体特性参考RegLayout。 • src类型为float类型时，配置不生效。；mode: MaskMergeMode枚举类型。选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；S: 目的操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；V: 源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg0(输入): 源操作数。 类型为RegTensor。

约束：- 源操作数数据类型为float时，支持寄存器全部重叠；源操作数数据类型为half时，仅支持源操作数寄存器重叠。
- 本接口操作数为寄存器，不涉及地址对齐。
- 本接口不修改全局寄存器的值。
- 源操作数类型为half时，Vector计算单元一次计算只处理最多64个元素，mask的有效情况以输入数据类型为准，只有偶数位有效，有效位共128bit，参考下图

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscExpSub](../../../c_api/reg/compound_compute/asc_exp_sub_deprecated.md)（`related`）：废弃 C Reg 接口保持同一复合运算语义，可用于迁移旧 C 指针代码到 C++ Reg ExpSub。
- [ExpSub](../../memory_vector_compute/composite_compute/exp_sub_isasi.md)（`related`）：ExpSub 与《ExpSub》的实质衔接是：Reg 与 C API 的 ExpSub 实现同一 exp(src)-scalar 复合运算，可用于接口迁移和语义核对。
<!-- cannbot:related:end -->
