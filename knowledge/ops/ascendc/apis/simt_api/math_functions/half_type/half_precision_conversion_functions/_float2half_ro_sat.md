---
type: API
title: __float2half_ro_sat
description: 将浮点数转换为半精度浮点数，并遵循CAST_ODD模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float2half_ro_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2half_ro_sat

功能：将浮点数转换为半精度浮点数，并遵循CAST_ODD模式，返回转换后的值。

函数原型：half __float2half_ro_sat(const float x)

参数：x（输入）源操作数。

返回值：将输入遵循CAST_ODD模式转换成的半精度浮点数。本接口受全局饱和寄存器的影响，。特殊值：±0→0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Half](../../../../simd_api/c_api/reg/data_type_convert/asc_float2half.md)（`related`）：AscFloat2Half说明将float类型数据转换成half类型，并支持多种舍入模式与饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。
- [__float2half](_float2half.md)（`related`）：__float2half说明遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__float22half2_ro](_float22half2_ro.md)（`same_topic`）：__float22half2_ro 与《__float2half_ro_sat》的实质衔接是：__float22half2_ro 与 RO-sat、RD/RN/RNA/RU/RZ 变体共享 float2→half2 双 lane 窄化，只改变舍入或饱和；scalar RO 和反向 half2→float2 明确向量封装及转换方向。
- [__float22half2_ro_sat](_float22half2_ro_sat.md)（`same_topic`）：__float2half_ro_sat 与 __float22half2_ro_sat 都在饱和模式下按 CAST_ODD 做 float→half；后者把同一转换打包到 float2 的两个分量。
- [__float2half_rd_sat](_float2half_rd_sat.md)（`same_topic`）：__float2half_ro_sat说明将浮点数转换为半精度浮点数，并遵循CAST_ODD模式，返回转换后的值；对__float2half_rd_sat而言，这些转换保持 float→half 的同一源目的类型，只切换饱和开关与 rd/rn/rna/ro/ru/rz 舍入；C API 是跨执行模型的对应能力。
- [__float2half_rn](_float2half_rn.md)（`same_topic`）：焦点处理float→half RINT 转换及显式舍入/饱和变体；__float2half_ro_sat正文说明“将浮点数转换为半精度浮点数，并遵循CAST_ODD模式，返回转换后的值”。候选保持 float→half 类型对，只改变 RINT/ROUND/FLOOR/CEIL/TRUNC/ODD 与饱和模式。
- [__float2half_rn_sat](_float2half_rn_sat.md)（`same_topic`）：__float2half_rn_sat说明饱和模式下，将浮点数转换为半精度浮点数，并遵循CAST_RINT模式，返回转换后的值。
- [__float2half_rna_sat](_float2half_rna_sat.md)（`same_topic`）：__float2half_rna_sat说明将浮点数转换为半精度浮点数，并遵循CAST_ROUND模式，返回转换后的值。
- [__float2half_ro](_float2half_ro.md)（`same_topic`）：__float2half_ro说明遵循CAST_ODD模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__float2half_ru_sat](_float2half_ru_sat.md)（`same_topic`）：__float2half_ru_sat说明将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值。
- [__float2half_rz](_float2half_rz.md)（`same_topic`）：__float2half_ro_sat说明将浮点数转换为半精度浮点数，并遵循CAST_ODD模式，返回转换后的值。
- [__float2half_rz_sat](_float2half_rz_sat.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half_ro_sat》补充：将浮点数转换为半精度浮点数，并遵循CAST_ODD模式，返回转换后的值。
<!-- cannbot:related:end -->
