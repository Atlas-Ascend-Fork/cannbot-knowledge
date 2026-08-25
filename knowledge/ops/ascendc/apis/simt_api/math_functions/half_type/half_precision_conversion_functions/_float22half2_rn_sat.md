---
type: API
title: __float22half2_rn_sat
description: 饱和模式下，将float2类型数据的两个分量遵循CAST_RINT模式转换为半精度浮点数，返回转换后的half2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float22half2_rn_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22half2_rn_sat

功能：饱和模式下，将float2类型数据的两个分量遵循CAST_RINT模式转换为半精度浮点数，返回转换后的half2类型数据。

函数原型：half2 __float22half2_rn_sat(const float2 x)

参数：x（输入）源操作数。

返回值：饱和模式下将输入的两个分量遵循CAST_RINT模式转换成的half2类型数据。本接口受全局饱和寄存器的影响，。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__floats2half2_rn](_floats2half2_rn.md)（`related`）：__float22half2_rn_sat 与《__floats2half2_rn》的实质衔接是：float2→half2 RN 饱和接口与非饱和/其他舍入、双 float 拼装和反向 half2→float2 共享双 lane 窄化契约。
- [__half22float2](_half22float2.md)（`related`）：__float22half2_rn_sat 与《__half22float2》的实质衔接是：float2→half2 RN 饱和接口与非饱和/其他舍入、双 float 拼装和反向 half2→float2 共享双 lane 窄化契约。
- [__float22half2_rd_sat](_float22half2_rd_sat.md)（`same_topic`）：《__float22half2_rd_sat》说明将float2类型数据的两个分量遵循CAST_FLOOR模式转换为半精度浮点数，返回转换后的half2类型数据。；《__float22half2_rn_sat》说明饱和模式下，将float2类型数据的两个分量遵循CAST_RINT模式转换为半精度浮点数，返回转换后的half2类型数据。。二者在float2到half2的向下舍入与饱和是两个独立维度，同输入输出的非饱和版和其他舍入版可直接对照上存在可执行的直接衔接。
- [__float22half2_rn](_float22half2_rn.md)（`same_topic`）：__float22half2_rn_sat 与《__float22half2_rn》的实质衔接是：float2→half2 RN 饱和接口与非饱和/其他舍入、双 float 拼装和反向 half2→float2 共享双 lane 窄化契约。
- [__float22half2_rna_sat](_float22half2_rna_sat.md)（`same_topic`）：__float22half2_rn_sat 与《__float22half2_rna_sat》的实质衔接是：float2→half2 RN 饱和接口与非饱和/其他舍入、双 float 拼装和反向 half2→float2 共享双 lane 窄化契约。
- [__float22half2_ro_sat](_float22half2_ro_sat.md)（`same_topic`）：《__float22half2_ro_sat》说明饱和模式下，将float2类型数据的两个分量遵循CAST_ODD模式转换为半精度浮点数，返回转换后的half2类型数据。；《__float22half2_rn_sat》说明饱和模式下，将float2类型数据的两个分量遵循CAST_RINT模式转换为半精度浮点数，返回转换后的half2类型数据。。二者在float2到half2的CAST_ODD饱和转换必须与同舍入非饱和版以及其他舍入模式的饱和/非饱和变体按CTRL与特殊值选择上存在可执行的直接衔接。
- [__float22half2_ru_sat](_float22half2_ru_sat.md)（`same_topic`）：“__float22half2_ru_sat”处理将float2类型数据的两个分量遵循CAST_CEIL模式转换为半精度浮点数，返回转换后的half2类型数据。；“__float22half2_rn_sat”明确饱和模式下，将float2类型数据的两个分量遵循CAST_RINT模式转换为半精度浮点数，返回转换后的half2类型数据。。实质衔接：这些接口保持 float2→half2 转换不变，仅切换饱和、标量/向量和舍入模式，可直接确认 ru_sat 的邻接选择。
- [__float22half2_rz_sat](_float22half2_rz_sat.md)（`same_topic`）：__float22half2_rn_sat 提供最近偶数舍入的饱和 packed 转换，与 focal 的向零模式适配不同精度策略。
<!-- cannbot:related:end -->
