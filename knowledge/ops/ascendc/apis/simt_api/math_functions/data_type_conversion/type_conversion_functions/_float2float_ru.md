---
type: API
title: __float2float_ru
description: 将浮点数四舍五入取整，并遵循CAST_CEIL模式。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2float_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2float_ru

功能：将浮点数四舍五入取整，并遵循CAST_CEIL模式。

函数原型：float __float2float_ru(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式取整后的浮点数。特殊值：±0→0；nan→nan；inf→inf；-inf→-inf；ASCRT_MIN_DENORM_F→1.0。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [类型转换函数](type_conversion_functions.md)（`related`）：__float2float_ru 与《类型转换函数》的实质衔接是：__float2float_ru 对 float 做向上取整；RN/RD/RNA/RZ 变体、类型转换总览和 AscFloat2float 直接对照五种舍入方向与特殊值。
- [AscFloat2float](../../../../simd_api/c_api/vector_compute/asc_float2float.md)（`same_topic`）：__float2float_ru 与《AscFloat2float》的实质衔接是：__float2float_ru 对 float 做向上取整；RN/RD/RNA/RZ 变体、类型转换总览和 AscFloat2float 直接对照五种舍入方向与特殊值。
- [__float2float_rd](_float2float_rd.md)（`same_topic`）：__float2float_ru 与《__float2float_rd》的实质衔接是：__float2float_ru 对 float 做向上取整；RN/RD/RNA/RZ 变体、类型转换总览和 AscFloat2float 直接对照五种舍入方向与特殊值。
- [__float2float_rn](_float2float_rn.md)（`same_topic`）：__float2float_ru 与《__float2float_rn》的实质衔接是：__float2float_ru 对 float 做向上取整；RN/RD/RNA/RZ 变体、类型转换总览和 AscFloat2float 直接对照五种舍入方向与特殊值。
- [__float2float_rna](_float2float_rna.md)（`same_topic`）：__float2float_ru 与《__float2float_rna》的实质衔接是：__float2float_ru 对 float 做向上取整；RN/RD/RNA/RZ 变体、类型转换总览和 AscFloat2float 直接对照五种舍入方向与特殊值。
- [__float2float_rz](_float2float_rz.md)（`same_topic`）：__float2float_ru 与《__float2float_rz》的实质衔接是：__float2float_ru 对 float 做向上取整；RN/RD/RNA/RZ 变体、类型转换总览和 AscFloat2float 直接对照五种舍入方向与特殊值。
<!-- cannbot:related:end -->
