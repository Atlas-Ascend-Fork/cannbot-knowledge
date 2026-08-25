---
type: API
title: __uint2half_ru
description: 遵循CAST_CEIL模式，将uint32类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__uint2half_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __uint2half_ru

功能：遵循CAST_CEIL模式，将uint32类型数据转换为half类型数据，返回转换后的值。

函数原型：half __uint2half_ru(const unsigned int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式转换成的half类型数据。特殊值：0→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__uint2half_rd](_uint2half_rd.md)（`same_topic`）：__uint2half_ru 与《__uint2half_rd》的实质衔接是：uint 到 half 的 RU/RN/RD/RZ/RNA 饱和变体只改变舍入方向，共同界定无符号整数转半精度的选择边界。
- [__uint2half_rn](_uint2half_rn.md)（`same_topic`）：__uint2half_ru 与《__uint2half_rn》的实质衔接是：uint 到 half 的 RU/RN/RD/RZ/RNA 饱和变体只改变舍入方向，共同界定无符号整数转半精度的选择边界。
- [__uint2half_rna](_uint2half_rna.md)（`same_topic`）：__uint2half_rna 与《__uint2half_ru》的实质衔接是：这些接口共享 uint32→half 输入输出契约，RNA/RN/RD/RU/RZ 及 SAT 变体只改变中点舍入和溢出处理。
- [__uint2half_ru_sat](_uint2half_ru_sat.md)（`same_topic`）：__uint2half_ru_sat 与《__uint2half_ru》的实质衔接是：这些接口共享 uint32→half 的饱和窄化，RU/RZ/RD/RN/RNA 及 non-SAT RU 只改变舍入方向和溢出结果。
- [__uint2half_rz](_uint2half_rz.md)（`same_topic`）：RU 对同一无符号转换向上舍入，与 RZ 在非精确可表示值上给出相反边界。
<!-- cannbot:related:end -->
