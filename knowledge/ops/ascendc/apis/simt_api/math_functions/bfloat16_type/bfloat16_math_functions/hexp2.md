---
type: API
title: Hexp2
description: 计算bfloat16_t输入x的2的x次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hexp2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hexp2

指定输入x，获取2的x次方。
函数原型：bfloat16_t hexp2(bfloat16_t x)
返回值：2的x次方。本接口受全局饱和模式影响，特殊值如下：
约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Exp2f](../../float_math_functions/exp2f.md)（`related`）：Hexp2 与《Exp2f》的实质衔接是：bfloat16 Hexp2 与 half、float 及双 lane Exp2 入口计算同一 2^x 任务，类型总览和各精度特殊值帮助选择返回宽度。
- [H2Exp2](../../half_type/half2_math_functions/h2exp2.md)（`related`）：Hexp2 与《H2Exp2》的实质衔接是：bfloat16 Hexp2 与 half、float 及双 lane Exp2 入口计算同一 2^x 任务，类型总览和各精度特殊值帮助选择返回宽度。
- [Hexp10](hexp10.md)（`related`）：Hexp2 与 Hexp10 仅指数底数不同，分别实现 2^x 与 10^x，可按缩放公式和数值范围选择。
- [Hexp2](../../half_type/half_math_functions/hexp2.md)（`related`）：Hexp2 与《Hexp2》的实质衔接是：bfloat16 Hexp2 与 half、float 及双 lane Exp2 入口计算同一 2^x 任务，类型总览和各精度特殊值帮助选择返回宽度。
- [BFloat16数学函数hexp](hexp.md)（`same_topic`）：BFloat16数学函数hexp 与《Hexp2》的实质衔接是：hexp 计算 bfloat16 标量 e^x；exp2/exp10、half、packed bfloat16x2、float exp/expm1 入口直接区分底数、类型宽度和稳定公式。
- [H2Exp2](../bfloat16x2_math_functions/h2exp2.md)（`same_topic`）：Hexp2 与《H2Exp2》的实质衔接是：bfloat16 Hexp2 与 half、float 及双 lane Exp2 入口计算同一 2^x 任务，类型总览和各精度特殊值帮助选择返回宽度。
- [bfloat16类型数学库函数](bfloat16_math_functions.md)（`same_topic`）：Hexp2 与《bfloat16类型数学库函数》的实质衔接是：bfloat16 Hexp2 与 half、float 及双 lane Exp2 入口计算同一 2^x 任务，类型总览和各精度特殊值帮助选择返回宽度。
<!-- cannbot:related:end -->
