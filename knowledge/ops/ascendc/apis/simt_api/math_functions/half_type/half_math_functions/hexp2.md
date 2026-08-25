---
type: API
title: Hexp2
description: 计算half输入x的2的x次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hexp2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Hexp2

功能：指定输入x，获取2的x次方（即2^x），适用于half精度数据类型。

函数原型：half hexp2(half x)

参数：x（输入）源操作数。

返回值：2的x次方。特殊值：inf→inf；-inf→0；nan→nan。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Exp2](../half2_math_functions/h2exp2.md)（`related`）：H2Exp2 把相同 2^x 运算扩展到 half2 双分量，适合用 packed SIMD 替代两次标量 Hexp2。
- [Half数学函数hexp](hexp.md)（`related`）：Hexp 与 Hexp2 对同一 half 标量分别计算 e^x 和 2^x，特殊值和全局饱和行为存在差异；用于按指数底数选型。
- [Hexp2](../../bfloat16_type/bfloat16_math_functions/hexp2.md)（`related`）：Hexp2 与《Hexp2》的实质衔接是：bfloat16 Hexp2 与 half、float 及双 lane Exp2 入口计算同一 2^x 任务，类型总览和各精度特殊值帮助选择返回宽度。
<!-- cannbot:related:end -->
