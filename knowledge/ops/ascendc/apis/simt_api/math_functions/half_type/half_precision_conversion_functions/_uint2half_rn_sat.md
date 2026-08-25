---
type: API
title: __uint2half_rn_sat
description: 将uint32类型数据转换为half类型数据，并遵循CAST_RINT模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__uint2half_rn_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __uint2half_rn_sat

功能：将uint32类型数据转换为half类型数据，并遵循CAST_RINT模式，返回转换后的值。

函数原型：half __uint2half_rn_sat(const unsigned int x)

参数：x（输入）源操作数。

返回值：遵循CAST_RINT模式，将输入uint32数据转换成的half数据。特殊值：0→0。

约束：SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__uint2half_rz_sat](_uint2half_rz_sat.md)（`related`）：__uint2half_rz_sat 与《__uint2half_rn_sat》的实质衔接是：uint→half RZ 的饱和/非饱和以及 RU/RD/RN/RNA 饱和变体共享输出类型，互相对照可确定大整数的截断和边界行为。
- [__uint2half_rd_sat](_uint2half_rd_sat.md)（`same_topic`）：__uint2half_rn_sat 与《__uint2half_rd_sat》的实质衔接是：uint→half 的 RN 饱和/非饱和与 RNA/RD/RU/RZ 饱和变体共同确定溢出和舍入选择。
- [__uint2half_rn](_uint2half_rn.md)（`same_topic`）：__uint2half_rn_sat 与《__uint2half_rn》的实质衔接是：uint→half 的 RN 饱和/非饱和与 RNA/RD/RU/RZ 饱和变体共同确定溢出和舍入选择。
- [__uint2half_rna_sat](_uint2half_rna_sat.md)（`same_topic`）：__uint2half_rn_sat 与《__uint2half_rna_sat》的实质衔接是：uint→half 的 RN 饱和/非饱和与 RNA/RD/RU/RZ 饱和变体共同确定溢出和舍入选择。
- [__uint2half_ru_sat](_uint2half_ru_sat.md)（`same_topic`）：__uint2half_ru_sat 与《__uint2half_rn_sat》的实质衔接是：这些接口共享 uint32→half 的饱和窄化，RU/RZ/RD/RN/RNA 及 non-SAT RU 只改变舍入方向和溢出结果。
<!-- cannbot:related:end -->
