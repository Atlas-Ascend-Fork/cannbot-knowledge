---
type: API
title: Expm1f
description: 指定输入x，获取e的x次方减1。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/expm1f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Expm1f

功能：指定输入x，获取e的x次方减1。

函数原型：float expm1f(float x)

参数：x（输入）源操作数。

返回值：e的x次方减1。特殊值：inf→inf；-inf→-1.0；nan→nan。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持输入为Subnormal的场景：本接口内部实现使用到了expf，由于expf不支持Subnormal场景，当输入x处于Subnormal范围内时，返回值为0；当x为较大负数且expf的结果处于Subnormal范围内时，本接口最终结果为-1.0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [BFloat16数学函数hexp](../bfloat16_type/bfloat16_math_functions/hexp.md)（`same_topic`）：BFloat16数学函数hexp 与《Expm1f》的实质衔接是：hexp 计算 bfloat16 标量 e^x；exp2/exp10、half、packed bfloat16x2、float exp/expm1 入口直接区分底数、类型宽度和稳定公式。
- [Log1pf](log1pf.md)（`same_topic`）：Log1pf 与《Expm1f》的实质衔接是：Log1pf 计算 ln(1+x) 并保留 x 近零精度；logf 是直接但近零易损的等价表达，expm1f 是配套的稳定逆向公式。
- [数学函数expf](expf.md)（`same_topic`）：《数学函数expf》处理“根据输入x，获取e的x次方的计算结果。”。《Expm1f》明确提供“指定输入x，获取e的x次方减1。”，其参数、调用或验证步骤直接接入expf 与 Expm1 及跨 dtype 的自然指数实现之间的数值合同。
<!-- cannbot:related:end -->
