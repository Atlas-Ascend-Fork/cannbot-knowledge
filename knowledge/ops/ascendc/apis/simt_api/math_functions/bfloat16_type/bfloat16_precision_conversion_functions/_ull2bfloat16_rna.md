---
type: API
title: __ull2bfloat16_rna
description: 遵循CAST_ROUND模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__ull2bfloat16_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ull2bfloat16_rna

功能：遵循CAST_ROUND模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。

函数原型：bfloat16_t __ull2bfloat16_rna(const unsigned long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的bfloat16类型数据。特殊值：0→0；257→258；511→512；65792→66048；18446744073709551615（ULLONG_MAX）→1.84467e+19。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__ull2half_rna](../../half_type/half_precision_conversion_functions/_ull2half_rna.md)（`related`）：__ull2half_rna 与《__ull2bfloat16_rna》的实质衔接是：uint64→half RNA 与其他舍入、有符号、bfloat16/float 目标变体共享大整数输入；UINT64 量化卡提供实际位宽约束。
- [__ull2bfloat16_rd](_ull2bfloat16_rd.md)（`same_topic`）：__ull2bfloat16_rd 与《__ull2bfloat16_rna》的实质衔接是：uint64→bfloat16 的 RD 与 RN/RNA/RU/RZ 及有符号/uint32 对应变体共享目标格式；量化故障提供 UINT64 输入的真实应用约束。
- [__ull2bfloat16_rn](_ull2bfloat16_rn.md)（`same_topic`）：《__ull2bfloat16_rn》说明遵循CAST_RINT模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。；《__ull2bfloat16_rna》说明遵循CAST_ROUND模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。。二者在uint64到bfloat16的目标类型固定，四种舍入模式是同一转换合同的互斥选择上存在可执行的直接衔接。
- [__ull2bfloat16_ru](_ull2bfloat16_ru.md)（`same_topic`）：__ull2bfloat16_ru 与《__ull2bfloat16_rna》的实质衔接是：uint64→bfloat16 RU 与 RD/RN/RNA/RZ、有符号和 uint32 变体共享目标格式；UINT64 量化卡提供实际位宽约束。
- [__ull2bfloat16_rz](_ull2bfloat16_rz.md)（`same_topic`）：《__ull2bfloat16_rz》说明遵循CAST_TRUNC模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。；《__ull2bfloat16_rna》说明遵循CAST_ROUND模式，将uint64类型数据转换为bfloat16类型数据，返回转换后的值。。二者在uint64到bfloat16的rz只改变舍入方向，同源同目标的rd/rn/rna/ru接口构成直接选择集合上存在可执行的直接衔接。
<!-- cannbot:related:end -->
