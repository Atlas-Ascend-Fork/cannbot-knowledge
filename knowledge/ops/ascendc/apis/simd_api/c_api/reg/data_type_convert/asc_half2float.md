---
type: API
title: AscHalf2Float
description: 将half类型数据转换为float类型，无舍入模式。 由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_half2float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscHalf2Float

将half类型数据转换为float类型，无舍入模式。

由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half。

约束：mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscHalf2float](../../vector_compute/asc_half2float.md)（`same_topic`）：将half类型转化为float类型，无舍入模式。；将half类型数据转换为float类型，无舍入模式。。两卡核心转换均为 half 到 float 且无舍入模式，分别覆盖 A2/A3 的 UB 向量接口与 950 的寄存器接口。
- [__half2float](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2float.md)（`same_topic`）：将half类型数据转换为float类型，无舍入模式。；功能：将half类型数据转换为浮点数，返回转换后的值。两页定义相同 half 到 float 转换语义，分别提供 Reg C API 与 SIMT 函数形式，便于按编程模型选接口。
<!-- cannbot:related:end -->
