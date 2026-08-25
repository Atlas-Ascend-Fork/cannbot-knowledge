---
type: API
title: __uint2bfloat16_ru
description: 遵循CAST_CEIL模式，将uint32类型数据转换为bfloat16类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__uint2bfloat16_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __uint2bfloat16_ru

功能：遵循CAST_CEIL模式，将uint32类型数据转换为bfloat16类型数据，返回转换后的值。

函数原型：bfloat16_t __uint2bfloat16_ru(const unsigned int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式转换成的bfloat16类型数据。特殊值：0→0；257→258；513→516；1025→1032；65537→66048；4294967295（UINT32_MAX）→4294967296。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__ull2bfloat16_ru](_ull2bfloat16_ru.md)（`related`）：__ull2bfloat16_ru 与《__uint2bfloat16_ru》的实质衔接是：uint64→bfloat16 RU 与 RD/RN/RNA/RZ、有符号和 uint32 变体共享目标格式；UINT64 量化卡提供实际位宽约束。
- [__int2bfloat16_ru](_int2bfloat16_ru.md)（`same_topic`）：__uint2bfloat16_ru 与《__int2bfloat16_ru》的实质衔接是：这些接口共享 uint32→bfloat16 输入输出，只改变 RU/RNA/RD/RN/RZ；signed int 与 uint64 的 RU 变体用于核对符号和输入宽度。
- [__uint2bfloat16_rd](_uint2bfloat16_rd.md)（`same_topic`）：__uint2bfloat16_ru 与《__uint2bfloat16_rd》的实质衔接是：这些接口共享 uint32→bfloat16 输入输出，只改变 RU/RNA/RD/RN/RZ；signed int 与 uint64 的 RU 变体用于核对符号和输入宽度。
- [__uint2bfloat16_rn](_uint2bfloat16_rn.md)（`same_topic`）：__uint2bfloat16_ru 与《__uint2bfloat16_rn》的实质衔接是：这些接口共享 uint32→bfloat16 输入输出，只改变 RU/RNA/RD/RN/RZ；signed int 与 uint64 的 RU 变体用于核对符号和输入宽度。
- [__uint2bfloat16_rna](_uint2bfloat16_rna.md)（`same_topic`）：__uint2bfloat16_ru 与《__uint2bfloat16_rna》的实质衔接是：这些接口共享 uint32→bfloat16 输入输出，只改变 RU/RNA/RD/RN/RZ；signed int 与 uint64 的 RU 变体用于核对符号和输入宽度。
- [__uint2bfloat16_rz](_uint2bfloat16_rz.md)（`same_topic`）：__uint2bfloat16_ru 与《__uint2bfloat16_rz》的实质衔接是：这些接口共享 uint32→bfloat16 输入输出，只改变 RU/RNA/RD/RN/RZ；signed int 与 uint64 的 RU 变体用于核对符号和输入宽度。
<!-- cannbot:related:end -->
