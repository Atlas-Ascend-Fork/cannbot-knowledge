---
type: API
title: 数学函数expf
description: 根据输入x，获取e的x次方的计算结果。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/expf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 数学函数expf

功能：根据输入x，获取e的x次方的计算结果。

函数原型：float expf(float x)

参数：x（输入）源操作数，数据类型为float。

返回值：e的x次方。特殊值：inf→inf；-inf→0；nan→nan。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Exp](../bfloat16_type/bfloat16x2_math_functions/h2exp.md)（`related`）：《数学函数expf》处理“根据输入x，获取e的x次方的计算结果。”。《H2Exp》明确提供“指定输入x，对x的各元素，获取e的该元素次方。”，其参数、调用或验证步骤直接接入expf 与 Expm1 及跨 dtype 的自然指数实现之间的数值合同。
- [BFloat16数学函数hexp](../bfloat16_type/bfloat16_math_functions/hexp.md)（`same_topic`）：hexp 与 expf 都计算 e^x；一个以 bfloat16 输入输出并受饱和/FTZ 约束，另一个使用 float，适合在同一指数函数主题下选择精度入口。
- [Expm1f](expm1f.md)（`same_topic`）：《数学函数expf》处理“根据输入x，获取e的x次方的计算结果。”。《Expm1f》明确提供“指定输入x，获取e的x次方减1。”，其参数、调用或验证步骤直接接入expf 与 Expm1 及跨 dtype 的自然指数实现之间的数值合同。
<!-- cannbot:related:end -->
