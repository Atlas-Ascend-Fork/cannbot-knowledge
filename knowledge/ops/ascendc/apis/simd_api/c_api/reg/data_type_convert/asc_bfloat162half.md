---
type: API
title: AscBfloat162Half
description: 将bfloat16_t类型转化为half类型，并支持多种舍入模式、饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_bfloat162half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscBfloat162Half

将bfloat16_t类型转化为half类型，并支持多种舍入模式、饱和/非饱和模式。

关于舍入模式和饱和/非饱和模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、half。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。
- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [__bfloat162half_rd_sat](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_bfloat162half_rd_sat.md)（`related`）：__bfloat162half_rd_sat 与《AscBfloat162Half》的实质衔接是：bfloat16→half 的 RD 饱和/非饱和及其他舍入饱和变体共享同一窄化契约，C API 是张量级对应入口。
- [__bfloat162half_rn](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_bfloat162half_rn.md)（`related`）：__bfloat162half_rn 与《AscBfloat162Half》的实质衔接是：这些接口都把 bfloat16 窄化为 half，差别只在 RN/RNA/RD/RU/RZ 与是否饱和；AscBfloat162Half 提供 Reg C API 的对应转换契约。
- [__bfloat162half_rna](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_bfloat162half_rna.md)（`related`）：__bfloat162half_rna 与《AscBfloat162Half》的实质衔接是：bfloat16 到 half 的各舍入/饱和变体共享同一窄化目标，互相对照可确定边界值与溢出行为。
- [__bfloat162half_rna_sat](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_bfloat162half_rna_sat.md)（`related`）：__bfloat162half_rna_sat 与《AscBfloat162Half》的实质衔接是：这些接口都把 bfloat16 按 RNA 窄化到 half；non-SAT、其他舍入的 SAT 变体和 AscBfloat162Half 直接对照饱和及特殊值。
- [__bfloat162half_ru_sat](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_bfloat162half_ru_sat.md)（`related`）：__bfloat162half_ru_sat 与《AscBfloat162Half》的实质衔接是：bfloat16→half RU 饱和/非饱和及其他舍入饱和变体共享同一窄化任务，AscBfloat16ToHalf 是 Reg 层对应入口；重点对照 CTRL 饱和失效时的结果。
- [__bfloat162half_rz](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_bfloat162half_rz.md)（`related`）：__bfloat162half_rz 与《AscBfloat162Half》的实质衔接是：这些接口都把 bfloat16 窄化为 half，RZ 的 SAT/non-SAT、RD/RN/RNA/RU 和 AscBfloat162Half 直接对照舍入及特殊值。
<!-- cannbot:related:end -->
