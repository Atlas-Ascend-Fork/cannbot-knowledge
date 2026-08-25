---
type: API
title: Exp10f
description: 指定输入x，获取10的x次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/exp10f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Exp10f

功能：指定输入x，获取10的x次方。

函数原型：float exp10f(float x)

参数：x（输入）源操作数。支持的数据类型为float。

返回值：10的x次方。特殊值：inf→inf；-inf→0；nan→nan。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Hexp10](../bfloat16_type/bfloat16_math_functions/hexp10.md)（`related`）：Hexp10 与 Exp10f 都计算 10^x，但分别处理 bfloat16_t 与 float；BF16 版本还明确 subnormal 刷零边界。
- [Hexp10](../half_type/half_math_functions/hexp10.md)（`related`）：Half Hexp10 是 Exp10f 的 FP16 标量对应接口，返回范围与 Inf/NaN 处理受 half 饱和上限约束。
- [H2Exp10](../half_type/half2_math_functions/h2exp10.md)（`same_topic`）：H2Exp10：H2Exp10 的 bfloat16x2同名接口和 half/float标量 exp10保持底数10，H2Exp/H2Exp2则直接帮助避免把 e^x、2^x 与10^x混用。 目标卡《Exp10f》补充：指定输入x，获取10的x次方。
<!-- cannbot:related:end -->
