---
type: API
title: __uint2half_rn
description: 遵循CAST_RINT模式，将uint32类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__uint2half_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __uint2half_rn

功能：遵循CAST_RINT模式，将uint32类型数据转换为half类型数据，返回转换后的值。

函数原型：half __uint2half_rn(const unsigned int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的half类型数据。特殊值：0→0；2049→2048；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；65505→ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__uint2half_rd](_uint2half_rd.md)（`same_topic`）：__uint2half_rd 与《__uint2half_rn》的实质衔接是：uint→half 向下舍入的饱和形态与 RN/RNA/RU/RZ 变体共同定义溢出处理和舍入选择。
- [__uint2half_rn_sat](_uint2half_rn_sat.md)（`same_topic`）：__uint2half_rn_sat 与《__uint2half_rn》的实质衔接是：uint→half 的 RN 饱和/非饱和与 RNA/RD/RU/RZ 饱和变体共同确定溢出和舍入选择。
- [__uint2half_rna](_uint2half_rna.md)（`same_topic`）：__uint2half_rna 与《__uint2half_rn》的实质衔接是：这些接口共享 uint32→half 输入输出契约，RNA/RN/RD/RU/RZ 及 SAT 变体只改变中点舍入和溢出处理。
- [__uint2half_ru](_uint2half_ru.md)（`same_topic`）：__uint2half_ru 与《__uint2half_rn》的实质衔接是：uint 到 half 的 RU/RN/RD/RZ/RNA 饱和变体只改变舍入方向，共同界定无符号整数转半精度的选择边界。
- [__uint2half_rz](_uint2half_rz.md)（`same_topic`）：RN 保持 uint32→half 契约并采用最近偶数舍入，与 focal 的 RZ 截断语义直接对照。
<!-- cannbot:related:end -->
