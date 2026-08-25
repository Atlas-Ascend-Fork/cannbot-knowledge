---
type: API
title: Hexp10
description: 计算half输入x的10的x次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hexp10.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Hexp10

功能：指定输入x，获取10的x次方。

函数原型：half hexp10(half x)

参数：x（输入）源操作数。

返回值：10的x次方。本接口受全局饱和寄存器的影响，。特殊值：±0→1；inf→ASCRT_MAX_NORMAL_FP16；-inf→0；nan→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Exp10f](../../float_math_functions/exp10f.md)（`related`）：Half Hexp10 是 Exp10f 的 FP16 标量对应接口，返回范围与 Inf/NaN 处理受 half 饱和上限约束。
- [Hexp10](../../bfloat16_type/bfloat16_math_functions/hexp10.md)（`related`）：bfloat16 Hexp10 与 focal 数学语义相同但精度类型不同，可用于 half 与 bfloat16 计算路径选型。
- [H2Exp10](../half2_math_functions/h2exp10.md)（`same_topic`）：H2Exp10：H2Exp10 的 bfloat16x2同名接口和 half/float标量 exp10保持底数10，H2Exp/H2Exp2则直接帮助避免把 e^x、2^x 与10^x混用。 目标卡《Hexp10》补充：计算half输入x的10的x次方。
<!-- cannbot:related:end -->
