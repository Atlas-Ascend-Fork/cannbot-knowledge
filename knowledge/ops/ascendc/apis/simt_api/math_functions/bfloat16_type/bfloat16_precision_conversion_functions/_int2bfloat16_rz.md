---
type: API
title: __int2bfloat16_rz
description: 遵循CAST_TRUNC模式，将int32类型数据转换为bfloat16类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__int2bfloat16_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2bfloat16_rz

功能：遵循CAST_TRUNC模式，将int32类型数据转换为bfloat16类型数据，返回转换后的值。

函数原型：bfloat16_t __int2bfloat16_rz(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式转换成的bfloat16类型数据。特殊值：0→0；257→256；-257→-256；2147483647（INT32_MAX）→2139095040；-2147483648（INT32_MIN）→-2147483648（INT32_MIN）。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2bfloat16_rd](_int2bfloat16_rd.md)（`related`）：RD 与 RZ 输入输出相同，但负数时向负无穷与向零结果不同。
- [__int2bfloat16_rn](_int2bfloat16_rn.md)（`related`）：RZ 向零截断，尤其负数与 FLOOR 不同；它与 RN 一起覆盖是否允许方向性偏差的选择。
- [__int2bfloat16_rna](_int2bfloat16_rna.md)（`same_topic`）：__int2bfloat16_rna 与《__int2bfloat16_rz》的实质衔接是：int 到 bfloat16 RNA 转换需对照其他舍入方向、SAT 和不同输入/输出类型确定边界。
- [__int2bfloat16_ru](_int2bfloat16_ru.md)（`same_topic`）：RZ 与 RU 提供同一转换的向零和向上舍入，负数及中点附近结果不同。
<!-- cannbot:related:end -->
