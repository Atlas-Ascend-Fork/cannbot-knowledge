---
type: API
title: __float2half_ru_sat
description: 将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float2half_ru_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2half_ru_sat

功能：将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值。

函数原型：half __float2half_ru_sat(const float x)

参数：x（输入）源操作数。

返回值：将输入遵循CAST_CEIL模式转换成的半精度浮点数。本接口受全局饱和寄存器的影响，。特殊值：±0→±0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float22half2_ru_sat](_float22half2_ru_sat.md)（`related`）：“__float22half2_ru_sat”处理将float2类型数据的两个分量遵循CAST_CEIL模式转换为半精度浮点数，返回转换后的half2类型数据。；“__float2half_ru_sat”明确将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值。。实质衔接：这些接口保持 float2→half2 转换不变，仅切换饱和、标量/向量和舍入模式，可直接确认 ru_sat 的邻接选择。
- [__float2half_rd_sat](_float2half_rd_sat.md)（`same_topic`）：__float2half_ru_sat说明将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值；对__float2half_rd_sat而言，这些转换保持 float→half 的同一源目的类型，只切换饱和开关与 rd/rn/rna/ro/ru/rz 舍入；C API 是跨执行模型的对应能力。
- [__float2half_rn](_float2half_rn.md)（`same_topic`）：焦点处理float→half RINT 转换及显式舍入/饱和变体；__float2half_ru_sat正文说明“将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值”。候选保持 float→half 类型对，只改变 RINT/ROUND/FLOOR/CEIL/TRUNC/ODD 与饱和模式。
- [__float2half_rn_sat](_float2half_rn_sat.md)（`same_topic`）：rn_sat 与 ru_sat 共享饱和契约但采用最近偶数/向上舍入，可按 rounding oracle 选择。
- [__float2half_ro_sat](_float2half_ro_sat.md)（`same_topic`）：__float2half_ru_sat说明将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值。
- [__float2half_ru](_float2half_ru.md)（`same_topic`）：__float2half_ru：所选接口保持 float→half 类型对不变，只切换 RU 的饱和版或 RD/RN/RNA/RO/RZ舍入，可直接比较特殊值和边界输出。 目标卡《__float2half_ru_sat》补充：将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值。
- [__float2half_rz](_float2half_rz.md)（`same_topic`）：__float2half_ru_sat说明将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值。
- [__float2half_rz_sat](_float2half_rz_sat.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half_ru_sat》补充：将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值。
<!-- cannbot:related:end -->
