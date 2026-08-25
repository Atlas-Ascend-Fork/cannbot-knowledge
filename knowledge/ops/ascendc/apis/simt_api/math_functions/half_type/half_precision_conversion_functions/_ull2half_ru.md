---
type: API
title: __ull2half_ru
description: 遵循CAST_CEIL模式，将uint64类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__ull2half_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ull2half_ru

功能：遵循CAST_CEIL模式，将uint64类型数据转换为half类型数据，返回转换后的值。

函数原型：half __ull2half_ru(const unsigned long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式转换成的half类型数据。本接口受全局饱和寄存器影响，。特殊值：0→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__ull2float_ru](../../data_type_conversion/type_conversion_functions/_ull2float_ru.md)（`related`）：__ull2float_ru 与《__ull2half_ru》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
- [__ull2half_rd](_ull2half_rd.md)（`same_topic`）：《__ull2half_ru》说明遵循CAST_CEIL模式，将uint64类型数据转换为half类型数据，返回转换后的值。；《__ull2half_rd》说明遵循CAST_FLOOR模式，将uint64类型数据转换为half类型数据，返回转换后的值。。二者在uint64到half的ru只改变舍入方向，同源同目标的rd/rn/rna/rz接口是直接选择集合上存在可执行的直接衔接。
- [__ull2half_rn](_ull2half_rn.md)（`same_topic`）：《__ull2half_ru》说明遵循CAST_CEIL模式，将uint64类型数据转换为half类型数据，返回转换后的值。；《__ull2half_rn》说明遵循CAST_RINT模式，将uint64类型数据转换为half类型数据，返回转换后的值。。二者在uint64到half的ru只改变舍入方向，同源同目标的rd/rn/rna/rz接口是直接选择集合上存在可执行的直接衔接。
- [__ull2half_rna](_ull2half_rna.md)（`same_topic`）：《__ull2half_ru》说明遵循CAST_CEIL模式，将uint64类型数据转换为half类型数据，返回转换后的值。；《__ull2half_rna》说明遵循CAST_ROUND模式，将uint64类型数据转换为half类型数据，返回转换后的值。。二者在uint64到half的ru只改变舍入方向，同源同目标的rd/rn/rna/rz接口是直接选择集合上存在可执行的直接衔接。
- [__ull2half_rz](_ull2half_rz.md)（`same_topic`）：《__ull2half_ru》说明遵循CAST_CEIL模式，将uint64类型数据转换为half类型数据，返回转换后的值。；《__ull2half_rz》说明遵循CAST_TRUNC模式，将uint64类型数据转换为half类型数据，返回转换后的值。。二者在uint64到half的ru只改变舍入方向，同源同目标的rd/rn/rna/rz接口是直接选择集合上存在可执行的直接衔接。
<!-- cannbot:related:end -->
