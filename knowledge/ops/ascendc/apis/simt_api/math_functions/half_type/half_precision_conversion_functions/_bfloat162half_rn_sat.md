---
type: API
title: __bfloat162half_rn_sat
description: 将bfloat16类型数据转换为half类型数据，并遵循CAST_RINT模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__bfloat162half_rn_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162half_rn_sat

功能：将bfloat16类型数据转换为half类型数据，并遵循CAST_RINT模式，返回转换后的值。

函数原型：half __bfloat162half_rn_sat(const bfloat16_t x)

参数：x（输入）源操作数。

返回值：将输入遵循CAST_RINT模式转换成的half类型数据。本接口受全局饱和寄存器的影响，。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__bfloat162half_rd_sat](_bfloat162half_rd_sat.md)（`same_topic`）：__bfloat162half_rd_sat 与《__bfloat162half_rn_sat》的实质衔接是：bfloat16→half 的 RD 饱和/非饱和及其他舍入饱和变体共享同一窄化契约，C API 是张量级对应入口。
- [__bfloat162half_rn](_bfloat162half_rn.md)（`same_topic`）：__bfloat162half_rn 与《__bfloat162half_rn_sat》的实质衔接是：这些接口都把 bfloat16 窄化为 half，差别只在 RN/RNA/RD/RU/RZ 与是否饱和；AscBfloat162Half 提供 Reg C API 的对应转换契约。
- [__bfloat162half_rna_sat](_bfloat162half_rna_sat.md)（`same_topic`）：__bfloat162half_rna_sat 与《__bfloat162half_rn_sat》的实质衔接是：这些接口都把 bfloat16 按 RNA 窄化到 half；non-SAT、其他舍入的 SAT 变体和 AscBfloat162Half 直接对照饱和及特殊值。
- [__bfloat162half_ru_sat](_bfloat162half_ru_sat.md)（`same_topic`）：__bfloat162half_ru_sat 与《__bfloat162half_rn_sat》的实质衔接是：bfloat16→half RU 饱和/非饱和及其他舍入饱和变体共享同一窄化任务，AscBfloat16ToHalf 是 Reg 层对应入口；重点对照 CTRL 饱和失效时的结果。
- [__bfloat162half_rz_sat](_bfloat162half_rz_sat.md)（`same_topic`）：RN_SAT 保持饱和转换，仅改为最近偶数舍入，供与 RZ_SAT 比较普通边界值。
<!-- cannbot:related:end -->
