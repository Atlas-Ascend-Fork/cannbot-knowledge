---
type: API
title: BFloat16数学函数hexp
description: 指定输入x，获取e的x次方。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hexp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BFloat16数学函数hexp

指定输入x，获取e的x次方。
函数原型：bfloat16_t hexp(bfloat16_t x)
返回值：e的x次方。本接口受全局饱和模式影响，特殊值如下：
约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Hexp10](hexp10.md)（`related`）：Hexp 计算 e^x，与 Hexp10 共同覆盖自然指数和十进制指数转换需求，并共享 FTZ 特殊值边界。
- [Expm1f](../../float_math_functions/expm1f.md)（`same_topic`）：BFloat16数学函数hexp 与《Expm1f》的实质衔接是：hexp 计算 bfloat16 标量 e^x；exp2/exp10、half、packed bfloat16x2、float exp/expm1 入口直接区分底数、类型宽度和稳定公式。
- [H2Exp](../bfloat16x2_math_functions/h2exp.md)（`same_topic`）：《H2Exp》处理“指定输入x，对x的各元素，获取e的该元素次方。”。《BFloat16数学函数hexp》明确提供“指定输入x，获取e的x次方。”，其参数、调用或验证步骤直接接入以 e 为底的 packed exp 与 scalar bfloat16/half2 对应实现。
- [Half数学函数hexp](../../half_type/half_math_functions/hexp.md)（`same_topic`）：BFloat16数学函数hexp 与《Half数学函数hexp》的实质衔接是：hexp 计算 bfloat16 标量 e^x；exp2/exp10、half、packed bfloat16x2、float exp/expm1 入口直接区分底数、类型宽度和稳定公式。
- [Hexp2](hexp2.md)（`same_topic`）：BFloat16数学函数hexp 与《Hexp2》的实质衔接是：hexp 计算 bfloat16 标量 e^x；exp2/exp10、half、packed bfloat16x2、float exp/expm1 入口直接区分底数、类型宽度和稳定公式。
- [数学函数expf](../../float_math_functions/expf.md)（`same_topic`）：hexp 与 expf 都计算 e^x；一个以 bfloat16 输入输出并受饱和/FTZ 约束，另一个使用 float，适合在同一指数函数主题下选择精度入口。
<!-- cannbot:related:end -->
