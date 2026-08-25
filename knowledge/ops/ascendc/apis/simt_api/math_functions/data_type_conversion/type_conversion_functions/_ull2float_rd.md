---
type: API
title: __ull2float_rd
description: 遵循CAST_FLOOR模式，将uint64类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__ull2float_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ull2float_rd

功能：遵循CAST_FLOOR模式，将uint64类型数据转换为浮点数，返回转换后的值。

函数原型：float __ull2float_rd(const unsigned long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的浮点数。特殊值：0→0；16777217（2^24+1）→16777216.0；4294967295（UINT32_MAX）→4294967040.0；18446744073709551615（UINT64_MAX）→2^64−2^40。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__half2ull_rd](../../half_type/half_precision_conversion_functions/_half2ull_rd.md)（`related`）：__half2ull_rd 与《__ull2float_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__ll2float_rd](_ll2float_rd.md)（`same_topic`）：__ull2float_rd 与《__ll2float_rd》的实质衔接是：这些转换保持 ull 到 float 的源目类型并改变舍入模式；ll/uint 的 rd 入口用于核对有符号性和源位宽对向下舍入结果的影响。
- [__uint2float_rd](_uint2float_rd.md)（`same_topic`）：__ull2float_rd 与《__uint2float_rd》的实质衔接是：这些转换保持 ull 到 float 的源目类型并改变舍入模式；ll/uint 的 rd 入口用于核对有符号性和源位宽对向下舍入结果的影响。
- [__ull2float_rn](_ull2float_rn.md)（`same_topic`）：__ull2float_rd 与《__ull2float_rn》的实质衔接是：这些转换保持 ull 到 float 的源目类型并改变舍入模式；ll/uint 的 rd 入口用于核对有符号性和源位宽对向下舍入结果的影响。
- [__ull2float_rna](_ull2float_rna.md)（`same_topic`）：__ull2float_rd 与《__ull2float_rna》的实质衔接是：这些转换保持 ull 到 float 的源目类型并改变舍入模式；ll/uint 的 rd 入口用于核对有符号性和源位宽对向下舍入结果的影响。
- [__ull2float_ru](_ull2float_ru.md)（`same_topic`）：__ull2float_ru 与《__ull2float_rd》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
- [__ull2float_rz](_ull2float_rz.md)（`same_topic`）：__ull2float_rd 与《__ull2float_rz》的实质衔接是：这些转换保持 ull 到 float 的源目类型并改变舍入模式；ll/uint 的 rd 入口用于核对有符号性和源位宽对向下舍入结果的影响。
<!-- cannbot:related:end -->
