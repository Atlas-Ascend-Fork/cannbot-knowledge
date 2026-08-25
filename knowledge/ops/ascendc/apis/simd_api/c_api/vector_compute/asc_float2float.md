---
type: API
title: AscFloat2float
description: 对float类型数据进行精度转换处理,支持多种舍入模式： - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入
  - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_float2float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscFloat2float

对float类型数据进行精度转换处理,支持多种舍入模式：
函数原型：void asc_float2float_rn(__ubuf__ float* dst, __ubuf__ float* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscFloor](../reg/data_type_convert/asc_floor.md)（`same_topic`）：AscFloat2float 与《AscFloor》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [Ceil](../../adv_api/math_compute/ceil_interface/ceil.md)（`same_topic`）：AscFloat2float 与《Ceil》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [Floor](../../adv_api/math_compute/floor_interface/floor.md)（`same_topic`）：AscFloat2float 与《Floor》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [Rint](../../adv_api/math_compute/rint_interface/rint.md)（`same_topic`）：AscFloat2float 与《Rint》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [Round](../../adv_api/math_compute/round_interface/round.md)（`same_topic`）：AscFloat2float 与《Round》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [Trunc](../../adv_api/math_compute/trunc_interface/trunc.md)（`same_topic`）：AscFloat2float 与《Trunc》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [__float2float_rd](../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2float_rd.md)（`same_topic`）：AscFloat2float 与《__float2float_rd》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [__float2float_rn](../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2float_rn.md)（`same_topic`）：AscFloat2float 与《__float2float_rn》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [__float2float_rna](../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2float_rna.md)（`same_topic`）：AscFloat2float 与《__float2float_rna》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [__float2float_ru](../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2float_ru.md)（`same_topic`）：__float2float_ru 与《AscFloat2float》的实质衔接是：__float2float_ru 对 float 做向上取整；RN/RD/RNA/RZ 变体、类型转换总览和 AscFloat2float 直接对照五种舍入方向与特殊值。
- [__float2float_rz](../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2float_rz.md)（`same_topic`）：AscFloat2float 与《__float2float_rz》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
<!-- cannbot:related:end -->
