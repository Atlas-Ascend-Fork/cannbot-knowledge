---
type: API
title: H2Log10
description: 获取以10为底，输入数据各元素的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2log10.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Log10

功能：获取以10为底，输入数据各元素的对数。

函数原型：half2 h2log10(half2 x)

参数：x（输入）源操作数。

返回值：以10为底的输入数据各元素的对数。本接口受全局饱和寄存器影响，。特殊值：±0→-ASCRT_MAX_NORMAL_FP16；inf→ASCRT_MAX_NORMAL_FP16；nan→0；-inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Log10](../../bfloat16_type/bfloat16x2_math_functions/h2log10.md)（`related`）：该接口实现同一 packed 双分量 log10，但数据类型为 half2；可用于 dtype 迁移并明确 BF16/FP16 最大有限值和头文件差异。
- [Hlog10](../../bfloat16_type/bfloat16_math_functions/hlog10.md)（`related`）：Hlog10 与《H2Log10》的实质衔接是：bfloat16 Hlog10 与 half、float、双 lane 和 Reg Log10 入口执行同一任务，类型总览用于对照特殊值和返回宽度。
- [Hlog10](../half_math_functions/hlog10.md)（`related`）：H2Log10 对 half2 两分量执行与 Hlog10 相同的常用对数；可按标量与 packed 双元素吞吐选择。
- [Log10](../../../../simd_api/basic_api/reg_vector_compute/basic_arithmetic/log10.md)（`related`）：Log10 与《H2Log10》的实质衔接是：Reg Log10 与 bfloat16/half/half2/float 的 log10 入口执行同一以 10 为底的对数任务，区别在执行模型和返回精度。
- [Log10f](../../float_math_functions/log10f.md)（`related`）：Log10f 与《H2Log10》的实质衔接是：Log10f 与 Reg、bfloat16、half 和 half2 的 log10 入口执行同一以 10 为底的对数，区别在执行模型和返回精度。
- [H2Log](h2log.md)（`same_topic`）：H2Log：H2Log、H2Log2、H2Log10分别计算e/2/10底对数，bfloat16x2同名接口提供类型变体；这些关系直接防止底数或数据类型选错。 目标卡《H2Log10》补充：获取以10为底，输入数据各元素的对数。
- [H2Log2](h2log2.md)（`same_topic`）：H2Log2 补充以 2 为底的同 dtype 双分量对数路径。
<!-- cannbot:related:end -->
