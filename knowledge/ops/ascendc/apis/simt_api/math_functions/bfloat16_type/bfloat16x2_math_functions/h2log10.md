---
type: API
title: H2Log10
description: 获取以10为底，输入数据各元素的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2log10.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Log10

功能：获取以10为底，输入数据各元素的对数。

函数原型：bfloat16x2_t h2log10(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：以10为底的输入数据各元素的对数。本接口受全局饱和模式影响，。特殊值：±0→-ASCRT_MAX_NORMAL_BF16；nan→0；inf→ASCRT_MAX_NORMAL_BF16；-inf→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Log](h2log.md)（`related`）：H2Log10 与 H2Log 共享 bfloat16x2 饱和和特殊值处理，仅对数底分别为 10 与 e；并读可按公式底数选型。
- [H2Log10](../../half_type/half2_math_functions/h2log10.md)（`related`）：该接口实现同一 packed 双分量 log10，但数据类型为 half2；可用于 dtype 迁移并明确 BF16/FP16 最大有限值和头文件差异。
- [H2Log2](h2log2.md)（`related`）：H2Log2 提供同一 bfloat16x2 输入的 2 为底对数，且特殊值/饱和模式与 H2Log10 可直接比较。
- [Hlog10](../bfloat16_math_functions/hlog10.md)（`related`）：Hlog10 与《H2Log10》的实质衔接是：bfloat16 Hlog10 与 half、float、双 lane 和 Reg Log10 入口执行同一任务，类型总览用于对照特殊值和返回宽度。
- [Hlog10](../../half_type/half_math_functions/hlog10.md)（`related`）：BF16x2 H2Log10 保持以 10 为底但采用 BF16 饱和值，用于 dtype 与 packed 宽度迁移。
- [Log10](../../../../simd_api/basic_api/reg_vector_compute/basic_arithmetic/log10.md)（`related`）：Log10 与《H2Log10》的实质衔接是：Reg Log10 与 bfloat16/half/half2/float 的 log10 入口执行同一以 10 为底的对数任务，区别在执行模型和返回精度。
- [Log10f](../../float_math_functions/log10f.md)（`related`）：Log10f 与《H2Log10》的实质衔接是：Log10f 与 Reg、bfloat16、half 和 half2 的 log10 入口执行同一以 10 为底的对数，区别在执行模型和返回精度。
<!-- cannbot:related:end -->
