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

- [AscHalf2float](../../vector_compute/asc_half2float.md)（`related`）：两者都将 half 转 float；focal 在 Reg API 中按 VL 的奇偶半段布局展开，vector 版本直接处理内存矢量，适合按数据驻留位置选型。
- [__low2float](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_low2float.md)（`related`）：AscHalf2Float 提供 Reg C API 的 half→float 向量转换，而 __low2float 是 SIMT packed 值的低 lane 标量提取，二者是迁移执行模型时的互补路径。
- [__half22float2](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half22float2.md)（`same_topic`）：AscHalf2Float说明将half类型数据转换为float类型，无舍入模式。 由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。
- [__half2float](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2float.md)（`same_topic`）：AscHalf2Float 与 __half2float 都执行无舍入的 half→float 扩展；前者按 mask 处理 Reg 向量，后者处理单个 SIMT 标量。
<!-- cannbot:related:end -->
