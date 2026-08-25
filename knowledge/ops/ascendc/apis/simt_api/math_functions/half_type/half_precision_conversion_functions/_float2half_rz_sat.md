---
type: API
title: __float2half_rz_sat
description: 饱和模式下，将浮点数转换为半精度浮点数，并遵循CAST_TRUNC模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float2half_rz_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2half_rz_sat

功能：饱和模式下，将浮点数转换为半精度浮点数，并遵循CAST_TRUNC模式，返回转换后的值。

函数原型：half __float2half_rz_sat(const float x)

参数：x（输入）源操作数。

返回值：饱和模式下将输入遵循CAST_TRUNC模式转换成的半精度浮点数。本接口受全局饱和寄存器的影响，。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float22half2_rz_sat](_float22half2_rz_sat.md)（`related`）：__float2half_rz_sat 是 focal 的标量版本，保持向零舍入与饱和，只处理单个 float。
- [__float2half](_float2half.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half》补充：遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__float2half_rd_sat](_float2half_rd_sat.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half_rd_sat》补充：将浮点数转换为half类型数据，并遵循CAST_FLOOR模式，返回转换后的值。
- [__float2half_rn](_float2half_rn.md)（`same_topic`）：焦点处理float→half RINT 转换及显式舍入/饱和变体；__float2half_rz_sat正文说明“饱和模式下，将浮点数转换为半精度浮点数，并遵循CAST_TRUNC模式，返回转换后的值”。候选保持 float→half 类型对，只改变 RINT/ROUND/FLOOR/CEIL/TRUNC/ODD 与饱和模式。
- [__float2half_rn_sat](_float2half_rn_sat.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half_rn_sat》补充：饱和模式下，将浮点数转换为半精度浮点数，并遵循CAST_RINT模式，返回转换后的值。
- [__float2half_rna_sat](_float2half_rna_sat.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half_rna_sat》补充：将浮点数转换为半精度浮点数，并遵循CAST_ROUND模式，返回转换后的值。
- [__float2half_ro_sat](_float2half_ro_sat.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half_ro_sat》补充：将浮点数转换为半精度浮点数，并遵循CAST_ODD模式，返回转换后的值。
- [__float2half_ru_sat](_float2half_ru_sat.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half_ru_sat》补充：将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值。
- [__float2half_rz](_float2half_rz.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half_rz》补充：遵循CAST_TRUNC模式，将浮点数转换为半精度浮点数，返回转换后的值。
<!-- cannbot:related:end -->
