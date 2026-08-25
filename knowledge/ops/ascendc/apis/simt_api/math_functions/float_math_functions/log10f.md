---
type: API
title: Log10f
description: 获取以10为底输入数据的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/log10f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Log10f

功能：获取以10为底，输入数据的对数。

函数原型：float log10f(float x)

参数：x（输入）源操作数。

返回值：以10为底的x的对数。特殊值：inf→inf；-inf→nan；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Log10](../bfloat16_type/bfloat16x2_math_functions/h2log10.md)（`related`）：Log10f 与《H2Log10》的实质衔接是：Log10f 与 Reg、bfloat16、half 和 half2 的 log10 入口执行同一以 10 为底的对数，区别在执行模型和返回精度。
- [H2Log10](../half_type/half2_math_functions/h2log10.md)（`related`）：Log10f 与《H2Log10》的实质衔接是：Log10f 与 Reg、bfloat16、half 和 half2 的 log10 入口执行同一以 10 为底的对数，区别在执行模型和返回精度。
- [Hlog10](../bfloat16_type/bfloat16_math_functions/hlog10.md)（`related`）：Log10f 与《Hlog10》的实质衔接是：Log10f 与 Reg、bfloat16、half 和 half2 的 log10 入口执行同一以 10 为底的对数，区别在执行模型和返回精度。
- [Hlog10](../half_type/half_math_functions/hlog10.md)（`related`）：Log10f 与《Hlog10》的实质衔接是：Log10f 与 Reg、bfloat16、half 和 half2 的 log10 入口执行同一以 10 为底的对数，区别在执行模型和返回精度。
- [Log10](../../../simd_api/basic_api/reg_vector_compute/basic_arithmetic/log10.md)（`related`）：Log10 与《Log10f》的实质衔接是：Reg Log10 与 bfloat16/half/half2/float 的 log10 入口执行同一以 10 为底的对数任务，区别在执行模型和返回精度。
<!-- cannbot:related:end -->
