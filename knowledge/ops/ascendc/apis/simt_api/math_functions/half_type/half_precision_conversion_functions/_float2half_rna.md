---
type: API
title: __float2half_rna
description: 遵循CAST_ROUND模式，将浮点数转换为半精度浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float2half_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2half_rna

功能：遵循CAST_ROUND模式，将浮点数转换为半精度浮点数，返回转换后的值。

函数原型：half __float2half_rna(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的半精度浮点数。本接口受全局饱和寄存器的影响，。特殊值：±0→±0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2half](../../../../simd_api/c_api/vector_compute/asc_float2half.md)（`related`）：AscFloat2half说明将 float 转换为 half，并支持 RINT、ROUND、FLOOR、CEIL、TRUNC 和 ODD 舍入模式。
- [__float2half](_float2half.md)（`same_topic`）：焦点处理float→half 的默认与显式舍入模式；__float2half_rna正文界定“遵循CAST_ROUND模式，将浮点数转换为半精度浮点数，返回转换后的值”。候选保持 float→half 类型对，只改变舍入方向或高阶/标量 API 入口。
- [__float2half_rd](_float2half_rd.md)（`same_topic`）：__float2half_rd说明遵循CAST_FLOOR模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__float2half_rn](_float2half_rn.md)（`same_topic`）：焦点处理float→half RINT 转换及显式舍入/饱和变体；__float2half_rna正文说明“遵循CAST_ROUND模式，将浮点数转换为半精度浮点数，返回转换后的值”。候选保持 float→half 类型对，只改变 RINT/ROUND/FLOOR/CEIL/TRUNC/ODD 与饱和模式。
- [__float2half_rna_sat](_float2half_rna_sat.md)（`same_topic`）：__float2half_rna_sat说明将浮点数转换为半精度浮点数，并遵循CAST_ROUND模式，返回转换后的值。
- [__float2half_ro](_float2half_ro.md)（`same_topic`）：__float2half_ro说明遵循CAST_ODD模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__float2half_ru](_float2half_ru.md)（`same_topic`）：__float2half_ru：所选接口保持 float→half 类型对不变，只切换 RU 的饱和版或 RD/RN/RNA/RO/RZ舍入，可直接比较特殊值和边界输出。 目标卡《__float2half_rna》补充：遵循CAST_ROUND模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__float2half_rz](_float2half_rz.md)（`same_topic`）：__float2half_rna说明遵循CAST_ROUND模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__half2half_rna](_half2half_rna.md)（`same_topic`）：__half2half_rna 与《__float2half_rna》的实质衔接是：同类型 rd/rn/ru/rz 与 bfloat16/float 输入的 rna/sat 变体共同界定 CAST_ROUND 的 tie-away 和饱和特殊值行为。
<!-- cannbot:related:end -->
