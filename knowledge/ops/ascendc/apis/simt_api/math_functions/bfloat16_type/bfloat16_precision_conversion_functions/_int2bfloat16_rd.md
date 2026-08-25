---
type: API
title: __int2bfloat16_rd
description: 遵循CAST_FLOOR模式，将int32类型数据转换为bfloat16类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__int2bfloat16_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2bfloat16_rd

功能：遵循CAST_FLOOR模式，将int32类型数据转换为bfloat16类型数据，返回转换后的值。

函数原型：bfloat16_t __int2bfloat16_rd(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的bfloat16类型数据。特殊值：0→0；2147483647（INT32_MAX）→2139095040；-2147483648（INT32_MIN）→-2147483648（INT32_MIN）。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2bfloat16_rn](_int2bfloat16_rn.md)（`related`）：与 RN 相同输入输出，但采用向负无穷取整；负数边界结果可能不同，需按数值契约选择。
- [__int2bfloat16_rna](_int2bfloat16_rna.md)（`related`）：__int2bfloat16_rna 与《__int2bfloat16_rd》的实质衔接是：int 到 bfloat16 RNA 转换需对照其他舍入方向、SAT 和不同输入/输出类型确定边界。
- [__int2bfloat16_ru](_int2bfloat16_ru.md)（`related`）：RU 向正无穷取整，与 RD 在正负输入边界上方向相反。
- [__int2bfloat16_rz](_int2bfloat16_rz.md)（`related`）：RD 与 RZ 输入输出相同，但负数时向负无穷与向零结果不同。
- [__uint2bfloat16_rd](_uint2bfloat16_rd.md)（`same_topic`）：__uint2bfloat16_rd 与《__int2bfloat16_rd》的实质衔接是：这些接口共享 uint32→bfloat16 输入输出，只改变 RD/RN/RNA/RU/RZ；有符号 int 的 RD 变体用于核对符号范围。
<!-- cannbot:related:end -->
