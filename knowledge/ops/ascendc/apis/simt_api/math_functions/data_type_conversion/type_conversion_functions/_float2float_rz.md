---
type: API
title: __float2float_rz
description: 将浮点数四舍五入取整，并遵循CAST_TRUNC模式。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2float_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2float_rz

功能：将浮点数四舍五入取整，并遵循CAST_TRUNC模式。

函数原型：float __float2float_rz(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式取整后的浮点数。特殊值：±0→0；±0.5→0；1.5→1.0；-1.5→-1.0；nan→nan；inf→inf；-inf→-inf。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Truncate](../../../../simd_api/basic_api/memory_vector_compute/type_conversion/truncate_isasi.md)（`related`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《__float2float_rz》明确“将浮点数四舍五入取整，并遵循CAST_TRUNC模式。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [AscFloat2float](../../../../simd_api/c_api/vector_compute/asc_float2float.md)（`same_topic`）：AscFloat2float 与《__float2float_rz》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [__float2float_rd](_float2float_rd.md)（`same_topic`）：同一 float 整数化的 floor 变体，与 RZ 在负值输入上形成关键差异。
- [__float2float_rn](_float2float_rn.md)（`same_topic`）：__float2float_rz 提供向零截断，是同一转换的 trunc 变体。
- [__float2float_rna](_float2float_rna.md)（`same_topic`）：RNA 提供半值远离零舍入，补充 RZ 之外的确定模式。
- [__float2float_ru](_float2float_ru.md)（`same_topic`）：__float2float_ru 与《__float2float_rz》的实质衔接是：__float2float_ru 对 float 做向上取整；RN/RD/RNA/RZ 变体、类型转换总览和 AscFloat2float 直接对照五种舍入方向与特殊值。
<!-- cannbot:related:end -->
