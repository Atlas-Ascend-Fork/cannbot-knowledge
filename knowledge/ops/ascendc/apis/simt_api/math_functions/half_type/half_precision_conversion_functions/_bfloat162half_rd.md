---
type: API
title: __bfloat162half_rd
description: 遵循CAST_FLOOR模式，将bfloat16类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__bfloat162half_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162half_rd

功能：遵循CAST_FLOOR模式，将bfloat16类型数据转换为half类型数据，返回转换后的值。

函数原型：half __bfloat162half_rd(const bfloat16_t x)

参数：x（输入）源操作数。

返回值：遵循CAST_FLOOR模式，将bfloat16类型数据转换成的half类型数据。本接口受全局饱和寄存器的影响，。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__bfloat162bfloat16_rd](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162bfloat16_rd.md)（`related`）：__bfloat162half_rd 从同一 bfloat16 源按 CAST_FLOOR 转到 half，适合对照 focal 保持 bfloat16 与跨格式转换的特殊值处理。
- [__bfloat162half_rd_sat](_bfloat162half_rd_sat.md)（`same_topic`）：__bfloat162half_rd_sat 与《__bfloat162half_rd》的实质衔接是：bfloat16→half 的 RD 饱和/非饱和及其他舍入饱和变体共享同一窄化契约，C API 是张量级对应入口。
- [__bfloat162half_rn](_bfloat162half_rn.md)（`same_topic`）：__bfloat162half_rn 与《__bfloat162half_rd》的实质衔接是：这些接口都把 bfloat16 窄化为 half，差别只在 RN/RNA/RD/RU/RZ 与是否饱和；AscBfloat162Half 提供 Reg C API 的对应转换契约。
- [__bfloat162half_rna](_bfloat162half_rna.md)（`same_topic`）：__bfloat162half_rna 与《__bfloat162half_rd》的实质衔接是：bfloat16 到 half 的各舍入/饱和变体共享同一窄化目标，互相对照可确定边界值与溢出行为。
- [__bfloat162half_ru](_bfloat162half_ru.md)（`same_topic`）：RD 为同一 bfloat16→half 转换提供向下舍入，与 RU 的单调方向相反。
- [__bfloat162half_rz](_bfloat162half_rz.md)（`same_topic`）：__bfloat162half_rz 与《__bfloat162half_rd》的实质衔接是：这些接口都把 bfloat16 窄化为 half，RZ 的 SAT/non-SAT、RD/RN/RNA/RU 和 AscBfloat162Half 直接对照舍入及特殊值。
<!-- cannbot:related:end -->
