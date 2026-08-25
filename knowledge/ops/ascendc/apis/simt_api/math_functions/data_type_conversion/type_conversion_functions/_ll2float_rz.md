---
type: API
title: __ll2float_rz
description: 遵循CAST_TRUNC模式，将int64类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__ll2float_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ll2float_rz

功能：遵循CAST_TRUNC模式，将int64类型数据转换为浮点数，返回转换后的值。

函数原型：float __ll2float_rz(const long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式转换成的浮点数。特殊值：0→0；16777217（2^24+1 ）→ASCRT_TWO_TO_24_F；-16777217（-2^24-1）→-ASCRT_TWO_TO_24_F；9223372036854775807（INT64_MAX）→9.22337149e+18；-9223372036854775808（INT64_MIN）→-9.22337204e+18。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2ll_rz](_float2ll_rz.md)（`same_topic`）：__float2ll_rz 与《__ll2float_rz》的实质衔接是：float→int64 RZ 与其他舍入、无符号和 half/bfloat16 变体共享饱和范围；Reg lane 错配卡验证 32→64 位宽变化的存储边界。
- [__ll2float_rd](_ll2float_rd.md)（`same_topic`）：__ll2float_rd说明遵循CAST_FLOOR模式，将int64类型数据转换为浮点数，返回转换后的值。
- [__ll2float_rn](_ll2float_rn.md)（`same_topic`）：__ll2float_rz说明遵循CAST_TRUNC模式，将int64类型数据转换为浮点数，返回转换后的值。
- [__ll2float_rna](_ll2float_rna.md)（`same_topic`）：__ll2float_rna：所选转换保持ll→float或RNA语义，只切换有符号性、源位宽和RD/RN/RU/RZ舍入，能直接核对大整数不可精确表示时的方向。 目标卡《__ll2float_rz》补充：遵循CAST_TRUNC模式，将int64类型数据转换为浮点数，返回转换后的值。
- [__ll2float_ru](_ll2float_ru.md)（`same_topic`）：__ll2float_ru说明遵循CAST_CEIL模式，将int64类型数据转换为浮点数，返回转换后的值。
<!-- cannbot:related:end -->
