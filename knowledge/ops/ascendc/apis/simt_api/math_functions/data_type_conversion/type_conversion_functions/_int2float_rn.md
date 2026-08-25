---
type: API
title: __int2float_rn
description: 遵循CAST_RINT模式，将int32类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__int2float_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2float_rn

功能：遵循CAST_RINT模式，将int32类型数据转换为浮点数，返回转换后的值。

函数原型：float __int2float_rn(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的浮点数。特殊值：0→0；2147483647 (INT32_MAX)→ASCRT_TWO_TO_31_F；-2147483648 (INT32_MIN)→-ASCRT_TWO_TO_31_F；16777217→ASCRT_TWO_TO_24_F；16777219→16777220.0。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2float_rna](_int2float_rna.md)（`related`）：“__int2float_rna”定义：遵循CAST_ROUND模式，将int32类型数据转换为浮点数，返回转换后的值。；“__int2float_rn”定义：遵循CAST_RINT模式，将int32类型数据转换为浮点数，返回转换后的值。。实质衔接：四张卡保持 int32→float，仅改变 RINT/CEIL/TRUNC/FLOOR；与焦点 RNA 的差异直接决定不可精确表示整数的舍入方向。
- [__int2float_rd](_int2float_rd.md)（`same_topic`）：rn 提供最近舍入，可与 floor 模式在不可精确表示整数上做精度选型。
- [__int2float_ru](_int2float_ru.md)（`same_topic`）：rn 提供最近舍入，可减少相对 floor/ceil 的绝对误差。
- [__int2float_rz](_int2float_rz.md)（`same_topic`）：__int2float_rn说明遵循CAST_RINT模式，将int32类型数据转换为浮点数，返回转换后的值。
<!-- cannbot:related:end -->
