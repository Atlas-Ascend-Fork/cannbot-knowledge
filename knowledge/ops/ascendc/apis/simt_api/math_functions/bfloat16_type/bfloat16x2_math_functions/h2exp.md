---
type: API
title: H2Exp
description: 指定输入x，对x的各元素，获取e的该元素次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2exp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Exp

功能：指定输入x，对x的各元素，获取e的该元素次方。

函数原型：bfloat16x2_t h2exp(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入的各元素，e的该元素次方。本接口受全局饱和模式影响，。特殊值：0→1.0；-0→1.0；nan→0；inf→ASCRT_MAX_NORMAL_BF16；-inf→0；ASCRT_MAX_NORMAL_BF16→ASCRT_MAX_NORMAL_BF16。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Exp2](h2exp2.md)（`related`）：H2Exp 与 H2Exp2 对同一 packed bfloat16x2 分别计算 e^x 与 2^x，特殊值和 subnormal 约束相近但底数不同。
- [数学函数expf](../../float_math_functions/expf.md)（`related`）：《数学函数expf》处理“根据输入x，获取e的x次方的计算结果。”。《H2Exp》明确提供“指定输入x，对x的各元素，获取e的该元素次方。”，其参数、调用或验证步骤直接接入expf 与 Expm1 及跨 dtype 的自然指数实现之间的数值合同。
- [BFloat16数学函数hexp](../bfloat16_math_functions/hexp.md)（`same_topic`）：《H2Exp》处理“指定输入x，对x的各元素，获取e的该元素次方。”。《BFloat16数学函数hexp》明确提供“指定输入x，获取e的x次方。”，其参数、调用或验证步骤直接接入以 e 为底的 packed exp 与 scalar bfloat16/half2 对应实现。
- [H2Exp](../../half_type/half2_math_functions/h2exp.md)（`same_topic`）：《H2Exp》处理“指定输入x，对x的各元素，获取e的该元素次方。”。《H2Exp》明确提供“指定输入x，对x的各元素，获取e的该元素次方。”，其参数、调用或验证步骤直接接入以 e 为底的 packed exp 与 scalar bfloat16/half2 对应实现。
<!-- cannbot:related:end -->
