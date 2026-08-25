---
type: API
title: Half数学函数hexp
description: 指定输入x，获取e的x次方。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hexp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Half数学函数hexp

功能：指定输入x，获取e的x次方。

函数原型：half hexp(half x)

参数：x（输入）源操作数。

返回值：e的x次方。本接口受全局饱和寄存器的影响，。特殊值：±0→1；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Hexp2](hexp2.md)（`related`）：Hexp 与 Hexp2 对同一 half 标量分别计算 e^x 和 2^x，特殊值和全局饱和行为存在差异；用于按指数底数选型。
- [BFloat16数学函数hexp](../../bfloat16_type/bfloat16_math_functions/hexp.md)（`same_topic`）：BFloat16数学函数hexp 与《Half数学函数hexp》的实质衔接是：hexp 计算 bfloat16 标量 e^x；exp2/exp10、half、packed bfloat16x2、float exp/expm1 入口直接区分底数、类型宽度和稳定公式。
<!-- cannbot:related:end -->
