---
type: API
title: Hlog10
description: 计算half输入数据以10为底的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hlog10.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Hlog10

功能：获取以10为底，输入数据的对数。

函数原型：half hlog10(half x)

参数：x（输入）源操作数。

返回值：以10为底的x的对数。本接口受全局饱和寄存器的影响，。特殊值：±0→-ASCRT_MAX_NORMAL_FP16；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Log10](../../bfloat16_type/bfloat16x2_math_functions/h2log10.md)（`related`）：BF16x2 H2Log10 保持以 10 为底但采用 BF16 饱和值，用于 dtype 与 packed 宽度迁移。
- [H2Log10](../half2_math_functions/h2log10.md)（`related`）：H2Log10 对 half2 两分量执行与 Hlog10 相同的常用对数；可按标量与 packed 双元素吞吐选择。
- [Half数学函数hlog](hlog.md)（`related`）：Hlog 与 Hlog10 处理相同 half 标量和相同饱和/特殊值域，但底数分别为 e 与 10；数学公式换底时必须区分。
- [Hlog10](../../bfloat16_type/bfloat16_math_functions/hlog10.md)（`related`）：Hlog10 与《Hlog10》的实质衔接是：bfloat16 Hlog10 与 half、float、双 lane 和 Reg Log10 入口执行同一任务，类型总览用于对照特殊值和返回宽度。
- [Hlog2](hlog2.md)（`related`）：Hlog2 提供以 2 为底的同 dtype 标量对数，与 Hlog10 共同覆盖按公式底数选型。
- [Log10](../../../../simd_api/basic_api/reg_vector_compute/basic_arithmetic/log10.md)（`related`）：Log10 与《Hlog10》的实质衔接是：Reg Log10 与 bfloat16/half/half2/float 的 log10 入口执行同一以 10 为底的对数任务，区别在执行模型和返回精度。
- [Log10f](../../float_math_functions/log10f.md)（`related`）：Log10f 与《Hlog10》的实质衔接是：Log10f 与 Reg、bfloat16、half 和 half2 的 log10 入口执行同一以 10 为底的对数，区别在执行模型和返回精度。
<!-- cannbot:related:end -->
