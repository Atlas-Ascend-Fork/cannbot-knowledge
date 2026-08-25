---
type: API
title: H2Exp
description: 指定输入x，对x的各元素，获取e的该元素次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2exp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Exp

功能：指定输入x，对x的各元素，获取e的该元素次方。

函数原型：half2 h2exp(half2 x)

参数：x（输入）源操作数。

返回值：输入的各元素，e的该元素次方。特殊值：±0→1；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→0；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Exp10](h2exp10.md)（`related`）：H2Exp10：H2Exp10 的 bfloat16x2同名接口和 half/float标量 exp10保持底数10，H2Exp/H2Exp2则直接帮助避免把 e^x、2^x 与10^x混用。 目标卡《H2Exp》补充：指定输入x，对x的各元素，获取e的该元素次方。
- [H2Tanh](h2tanh.md)（`related`）：tanh 可由 exp 组合，但 h2tanh 提供直接实现；拆解路径需单独验证溢出和精度。
- [H2Exp](../../bfloat16_type/bfloat16x2_math_functions/h2exp.md)（`same_topic`）：《H2Exp》处理“指定输入x，对x的各元素，获取e的该元素次方。”。《H2Exp》明确提供“指定输入x，对x的各元素，获取e的该元素次方。”，其参数、调用或验证步骤直接接入以 e 为底的 packed exp 与 scalar bfloat16/half2 对应实现。
- [H2Exp2](h2exp2.md)（`same_topic`）：H2Exp 使用 e 为底而 focal 使用 2 为底，是同一 half2 指数族按底数的直接选型。
<!-- cannbot:related:end -->
