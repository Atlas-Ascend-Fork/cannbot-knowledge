---
type: API
title: __ll2float_rd
description: 遵循CAST_FLOOR模式，将int64类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__ll2float_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ll2float_rd

功能：遵循CAST_FLOOR模式，将int64类型数据转换为浮点数，返回转换后的值。

函数原型：float __ll2float_rd(const long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的浮点数。特殊值：9223372036854775807（INT64_MAX）→9.223372e+18；-9223372036854775808（INT64_MIN）→-9.223372e+18；16777217（2^24+1 ）→ASCRT_TWO_TO_24_F；-16777217（-2^24-1）→-1.67772e+07；9007199254740993（2^53+1）→9.0072e+15；-9007199254740993（-2^53-1）→-9.0072e+15。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt642float](../../../../simd_api/c_api/vector_compute/asc_int642float.md)（`related`）：__ll2float_rd 是同一 FLOOR int64→float 的 SIMT 标量形式，提供 2^24/2^53 邻近整数的舍入例子，可作为线程标量实现和数值验证对照。
- [__ll2float_rn](_ll2float_rn.md)（`same_topic`）：__ll2float_rd说明遵循CAST_FLOOR模式，将int64类型数据转换为浮点数，返回转换后的值。
- [__ll2float_rna](_ll2float_rna.md)（`same_topic`）：__ll2float_rna：所选转换保持ll→float或RNA语义，只切换有符号性、源位宽和RD/RN/RU/RZ舍入，能直接核对大整数不可精确表示时的方向。 目标卡《__ll2float_rd》补充：遵循CAST_FLOOR模式，将int64类型数据转换为浮点数，返回转换后的值。
- [__ll2float_ru](_ll2float_ru.md)（`same_topic`）：rd 与 ru 对同一 int64→float 转换提供向下/向上取整边界。
- [__ll2float_rz](_ll2float_rz.md)（`same_topic`）：__ll2float_rd说明遵循CAST_FLOOR模式，将int64类型数据转换为浮点数，返回转换后的值。
- [__ull2float_rd](_ull2float_rd.md)（`same_topic`）：__ull2float_rd 与《__ll2float_rd》的实质衔接是：这些转换保持 ull 到 float 的源目类型并改变舍入模式；ll/uint 的 rd 入口用于核对有符号性和源位宽对向下舍入结果的影响。
<!-- cannbot:related:end -->
