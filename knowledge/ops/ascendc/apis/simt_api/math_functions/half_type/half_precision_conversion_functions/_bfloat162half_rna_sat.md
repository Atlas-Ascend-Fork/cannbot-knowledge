---
type: API
title: __bfloat162half_rna_sat
description: 将bfloat16类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__bfloat162half_rna_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162half_rna_sat

功能：将bfloat16类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。

函数原型：half __bfloat162half_rna_sat(const bfloat16_t x)

参数：x（输入）源操作数。

返回值：将输入遵循CAST_ROUND模式转换成的half类型数据。本接口受全局饱和寄存器的影响，。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16。

约束：SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscBfloat162Half](../../../../simd_api/c_api/reg/data_type_convert/asc_bfloat162half.md)（`related`）：__bfloat162half_rna_sat 与《AscBfloat162Half》的实质衔接是：这些接口都把 bfloat16 按 RNA 窄化到 half；non-SAT、其他舍入的 SAT 变体和 AscBfloat162Half 直接对照饱和及特殊值。
- [__bfloat162half_rd_sat](_bfloat162half_rd_sat.md)（`same_topic`）：__bfloat162half_rna_sat 与《__bfloat162half_rd_sat》的实质衔接是：这些接口都把 bfloat16 按 RNA 窄化到 half；non-SAT、其他舍入的 SAT 变体和 AscBfloat162Half 直接对照饱和及特殊值。
- [__bfloat162half_rn_sat](_bfloat162half_rn_sat.md)（`same_topic`）：__bfloat162half_rna_sat 与《__bfloat162half_rn_sat》的实质衔接是：这些接口都把 bfloat16 按 RNA 窄化到 half；non-SAT、其他舍入的 SAT 变体和 AscBfloat162Half 直接对照饱和及特殊值。
- [__bfloat162half_rna](_bfloat162half_rna.md)（`same_topic`）：__bfloat162half_rna_sat 与《__bfloat162half_rna》的实质衔接是：这些接口都把 bfloat16 按 RNA 窄化到 half；non-SAT、其他舍入的 SAT 变体和 AscBfloat162Half 直接对照饱和及特殊值。
- [__bfloat162half_ru_sat](_bfloat162half_ru_sat.md)（`same_topic`）：__bfloat162half_rna_sat 与《__bfloat162half_ru_sat》的实质衔接是：这些接口都把 bfloat16 按 RNA 窄化到 half；non-SAT、其他舍入的 SAT 变体和 AscBfloat162Half 直接对照饱和及特殊值。
- [__bfloat162half_rz_sat](_bfloat162half_rz_sat.md)（`same_topic`）：__bfloat162half_rna_sat 与《__bfloat162half_rz_sat》的实质衔接是：这些接口都把 bfloat16 按 RNA 窄化到 half；non-SAT、其他舍入的 SAT 变体和 AscBfloat162Half 直接对照饱和及特殊值。
- [__half2half_rna](_half2half_rna.md)（`same_topic`）：__half2half_rna 与《__bfloat162half_rna_sat》的实质衔接是：同类型 rd/rn/ru/rz 与 bfloat16/float 输入的 rna/sat 变体共同界定 CAST_ROUND 的 tie-away 和饱和特殊值行为。
<!-- cannbot:related:end -->
