---
type: API
title: __int2bfloat16_rn
description: 遵循CAST_RINT模式，将int32类型数据转换为bfloat16类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__int2bfloat16_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2bfloat16_rn

功能：遵循CAST_RINT模式，将int32类型数据转换为bfloat16类型数据，返回转换后的值。

函数原型：bfloat16_t __int2bfloat16_rn(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的bfloat16类型数据。特殊值：0→0；±257→±256；±259→±260；±514→±512；2147483647（INT32_MAX）→2.14748e+09；-2147483648（INT32_MIN）→-2.14748e+09。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2bfloat16_rd](_int2bfloat16_rd.md)（`related`）：与 RN 相同输入输出，但采用向负无穷取整；负数边界结果可能不同，需按数值契约选择。
- [__int2bfloat16_rz](_int2bfloat16_rz.md)（`related`）：RZ 向零截断，尤其负数与 FLOOR 不同；它与 RN 一起覆盖是否允许方向性偏差的选择。
- [__int2bfloat16_rna](_int2bfloat16_rna.md)（`same_topic`）：__int2bfloat16_rna 与《__int2bfloat16_rn》的实质衔接是：int 到 bfloat16 RNA 转换需对照其他舍入方向、SAT 和不同输入/输出类型确定边界。
- [__int2bfloat16_ru](_int2bfloat16_ru.md)（`same_topic`）：RN 与 RU 是同一 int→bfloat16 转换的最近偶数和向上舍入选项。
<!-- cannbot:related:end -->
