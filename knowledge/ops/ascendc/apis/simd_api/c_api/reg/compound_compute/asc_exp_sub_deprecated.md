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

- [ExpSub](../../../basic_api/memory_vector_compute/composite_compute/exp_sub_isasi.md)（`related`）：ExpSub 与《AscExpSub》的实质衔接是：Reg 与 C API 的 ExpSub 实现同一 exp(src)-scalar 复合运算，可用于接口迁移和语义核对。
- [ExpSub](../../../basic_api/reg_vector_compute/composite_compute/exp_sub.md)（`related`）：废弃 C Reg 接口保持同一复合运算语义，可用于迁移旧 C 指针代码到 C++ Reg ExpSub。
<!-- cannbot:related:end -->
