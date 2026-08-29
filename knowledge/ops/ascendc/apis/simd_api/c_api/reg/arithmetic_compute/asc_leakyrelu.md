---
type: API
title: AscLeakyrelu
description: 按元素执行Leaky ReLU操作，大于0的元素直接写入目的操作数，否则乘以标量value后写入。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_leakyrelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscLeakyrelu

该接口用于按元素执行Leaky ReLU（Leaky Rectified Linear Unit）操作：当源操作数中某元素大于0时，直接将该元素写入目的操作数；否则将该元素乘以标量值value后写入目的操作数。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscLeakyrelu](../../vector_compute/asc_leakyrelu.md)（`same_topic`）：执行矢量Leaky Relu运算。计算公式如下：；该接口用于按元素执行Leaky ReLU（Leaky Rectified Linear Unit）操作：当源操作数中某元素大于0时，直接将该元素写入目的操作数；否则将该元素乘以标量值value后写入目的操作数。。两卡是同一 C API LeakyReLU 语义的 A2/A3 UB 指针版与 950 寄存器 mask 版。
<!-- cannbot:related:end -->
