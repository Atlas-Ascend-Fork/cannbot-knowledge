---
type: API
title: AscAbsSub
description: 根据mask对源操作数src0和src1进行按元素相减再求绝对值，将结果写入dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compound_compute/asc_abs_sub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscAbsSub

根据mask对源操作数src0、src1进行按元素相减再求绝对值的操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数0（矢量数据寄存器）。；src1(输入): 源操作数1（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half。

约束：mask未筛选的元素在输出中置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AbsSub](../../../basic_api/memory_vector_compute/composite_compute/abs_sub_isasi.md)（`related`）：asc_abs_sub 提供同一减后取绝对值的 C Reg 接口及 mask 语义，是从 C++ Memory AbsSub 下沉到 C API Reg 编程的直接对应。
- [AbsSub](../../../basic_api/reg_vector_compute/composite_compute/abs_sub.md)（`related`）：AscAbsSub 是同一 Reg 硬件语义的 C API 入口，便于在 C 指针与 C++ RegTensor 路线间对照签名。
<!-- cannbot:related:end -->
