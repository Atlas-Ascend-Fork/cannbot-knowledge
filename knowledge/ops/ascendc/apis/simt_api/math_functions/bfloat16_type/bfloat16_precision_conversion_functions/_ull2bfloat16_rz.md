---
type: API
title: __ull2bfloat16_rz
description: 遵循CAST_TRUNC模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__ull2bfloat16_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ull2bfloat16_rz

功能：遵循CAST_TRUNC模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。

函数原型：bfloat16_t __ull2bfloat16_rz(const unsigned long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式转换成的bfloat16类型数据。特殊值：0→0；257→256；513→512；65537→65536；18446744073709551615（ULLONG_MAX）→1.84467e+19。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__ull2bfloat16_rd](_ull2bfloat16_rd.md)（`same_topic`）：《__ull2bfloat16_rz》说明遵循CAST_TRUNC模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。；《__ull2bfloat16_rd》说明遵循CAST_FLOOR模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。。二者在uint64到bfloat16的rz只改变舍入方向，同源同目标的rd/rn/rna/ru接口构成直接选择集合上存在可执行的直接衔接。
- [__ull2bfloat16_rn](_ull2bfloat16_rn.md)（`same_topic`）：《__ull2bfloat16_rz》说明遵循CAST_TRUNC模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。；《__ull2bfloat16_rn》说明遵循CAST_RINT模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。。二者在uint64到bfloat16的rz只改变舍入方向，同源同目标的rd/rn/rna/ru接口构成直接选择集合上存在可执行的直接衔接。
- [__ull2bfloat16_rna](_ull2bfloat16_rna.md)（`same_topic`）：《__ull2bfloat16_rz》说明遵循CAST_TRUNC模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。；《__ull2bfloat16_rna》说明遵循CAST_ROUND模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。。二者在uint64到bfloat16的rz只改变舍入方向，同源同目标的rd/rn/rna/ru接口构成直接选择集合上存在可执行的直接衔接。
- [__ull2bfloat16_ru](_ull2bfloat16_ru.md)（`same_topic`）：《__ull2bfloat16_rz》说明遵循CAST_TRUNC模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。；《__ull2bfloat16_ru》说明遵循CAST_CEIL模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。。二者在uint64到bfloat16的rz只改变舍入方向，同源同目标的rd/rn/rna/ru接口构成直接选择集合上存在可执行的直接衔接。
<!-- cannbot:related:end -->
