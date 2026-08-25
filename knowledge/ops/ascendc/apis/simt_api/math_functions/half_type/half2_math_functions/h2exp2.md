---
type: API
title: H2Exp2
description: 指定输入x，对x的各元素，获取2的该元素次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2exp2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Exp2

功能：指定输入x，对x的各元素，获取2的该元素次方。

函数原型：half2 h2exp2(half2 x)

参数：x（输入）源操作数。

返回值：输入的各元素，2的该元素次方。特殊值：±0→1；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Exp10](h2exp10.md)（`related`）：H2Exp10：H2Exp10 的 bfloat16x2同名接口和 half/float标量 exp10保持底数10，H2Exp/H2Exp2则直接帮助避免把 e^x、2^x 与10^x混用。 目标卡《H2Exp2》补充：指定输入x，对x的各元素，获取2的该元素次方。
- [H2Exp2](../../bfloat16_type/bfloat16x2_math_functions/h2exp2.md)（`related`）：bfloat16x2 与 half2 版本均逐分量计算 2^x，适合跨低精度 dtype 对照特殊值与误差。
- [Hexp2](../../bfloat16_type/bfloat16_math_functions/hexp2.md)（`related`）：Hexp2 与《H2Exp2》的实质衔接是：bfloat16 Hexp2 与 half、float 及双 lane Exp2 入口计算同一 2^x 任务，类型总览和各精度特殊值帮助选择返回宽度。
- [Hexp2](../half_math_functions/hexp2.md)（`related`）：H2Exp2 把相同 2^x 运算扩展到 half2 双分量，适合用 packed SIMD 替代两次标量 Hexp2。
- [H2Exp](h2exp.md)（`same_topic`）：H2Exp 使用 e 为底而 focal 使用 2 为底，是同一 half2 指数族按底数的直接选型。
<!-- cannbot:related:end -->
