---
type: API
title: __bfloat162half_ru
description: 遵循CAST_CEIL模式，将bfloat16类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__bfloat162half_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162half_ru

功能：遵循CAST_CEIL模式，将bfloat16类型数据转换为half类型数据，返回转换后的值。

函数原型：half __bfloat162half_ru(const bfloat16_t x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式转换成的half类型数据。本接口受全局饱和寄存器的影响，。特殊值：nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__bfloat162half_rd](_bfloat162half_rd.md)（`same_topic`）：RD 为同一 bfloat16→half 转换提供向下舍入，与 RU 的单调方向相反。
- [__bfloat162half_rn](_bfloat162half_rn.md)（`same_topic`）：__bfloat162half_rn 与《__bfloat162half_ru》的实质衔接是：这些接口都把 bfloat16 窄化为 half，差别只在 RN/RNA/RD/RU/RZ 与是否饱和；AscBfloat162Half 提供 Reg C API 的对应转换契约。
- [__bfloat162half_rna](_bfloat162half_rna.md)（`same_topic`）：RNA 为同一转换提供中点远离零规则，可用于需要传统四舍五入而非 RU 的场景。
- [__bfloat162half_ru_sat](_bfloat162half_ru_sat.md)（`same_topic`）：__bfloat162half_ru_sat 与《__bfloat162half_ru》的实质衔接是：bfloat16→half RU 饱和/非饱和及其他舍入饱和变体共享同一窄化任务，AscBfloat16ToHalf 是 Reg 层对应入口；重点对照 CTRL 饱和失效时的结果。
- [__bfloat162half_rz](_bfloat162half_rz.md)（`same_topic`）：__bfloat162half_rz 与《__bfloat162half_ru》的实质衔接是：这些接口都把 bfloat16 窄化为 half，RZ 的 SAT/non-SAT、RD/RN/RNA/RU 和 AscBfloat162Half 直接对照舍入及特殊值。
<!-- cannbot:related:end -->
