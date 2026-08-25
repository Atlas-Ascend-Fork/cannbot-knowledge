---
type: API
title: __int2bfloat16_rna
description: 遵循CAST_ROUND模式，将int32类型数据转换为bfloat16类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__int2bfloat16_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2bfloat16_rna

功能：遵循CAST_ROUND模式，将int32类型数据转换为bfloat16类型数据，返回转换后的值。

函数原型：bfloat16_t __int2bfloat16_rna(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的bfloat16类型数据。特殊值：2147483647（INT32_MAX）→2147483648；-2147483648（INT32_MIN）→-2147483648（INT32_MIN）；257→258；-257→-258。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2bfloat16_rd](_int2bfloat16_rd.md)（`related`）：__int2bfloat16_rna 与《__int2bfloat16_rd》的实质衔接是：int 到 bfloat16 RNA 转换需对照其他舍入方向、SAT 和不同输入/输出类型确定边界。
- [__int2bfloat16_rn](_int2bfloat16_rn.md)（`same_topic`）：__int2bfloat16_rna 与《__int2bfloat16_rn》的实质衔接是：int 到 bfloat16 RNA 转换需对照其他舍入方向、SAT 和不同输入/输出类型确定边界。
- [__int2bfloat16_ru](_int2bfloat16_ru.md)（`same_topic`）：__int2bfloat16_rna 与《__int2bfloat16_ru》的实质衔接是：int 到 bfloat16 RNA 转换需对照其他舍入方向、SAT 和不同输入/输出类型确定边界。
- [__int2bfloat16_rz](_int2bfloat16_rz.md)（`same_topic`）：__int2bfloat16_rna 与《__int2bfloat16_rz》的实质衔接是：int 到 bfloat16 RNA 转换需对照其他舍入方向、SAT 和不同输入/输出类型确定边界。
- [__uint2bfloat16_rna](_uint2bfloat16_rna.md)（`same_topic`）：__uint2bfloat16_rna 与《__int2bfloat16_rna》的实质衔接是：uint32→bfloat16 的 RNA 与 RN/RD/RU/RZ 变体共享输入输出，只改变舍入边界；int→bfloat16 RNA 提供符号输入的对应契约。
<!-- cannbot:related:end -->
