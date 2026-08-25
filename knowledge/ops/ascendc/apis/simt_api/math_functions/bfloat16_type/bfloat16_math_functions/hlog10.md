---
type: API
title: Hlog10
description: 计算bfloat16_t输入数据以10为底的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hlog10.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hlog10

获取以10为底，输入数据的对数。
函数原型：bfloat16_t hlog10(bfloat16_t x)
返回值：以10为底的x的对数。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [BFloat16数学函数hlog](hlog.md)（`related`）：Hlog10 补充十进制对数，与自然对数 Hlog 共同覆盖常用底数转换。
- [H2Log10](../bfloat16x2_math_functions/h2log10.md)（`related`）：Hlog10 与《H2Log10》的实质衔接是：bfloat16 Hlog10 与 half、float、双 lane 和 Reg Log10 入口执行同一任务，类型总览用于对照特殊值和返回宽度。
- [H2Log10](../../half_type/half2_math_functions/h2log10.md)（`related`）：Hlog10 与《H2Log10》的实质衔接是：bfloat16 Hlog10 与 half、float、双 lane 和 Reg Log10 入口执行同一任务，类型总览用于对照特殊值和返回宽度。
- [Hlog10](../../half_type/half_math_functions/hlog10.md)（`related`）：Hlog10 与《Hlog10》的实质衔接是：bfloat16 Hlog10 与 half、float、双 lane 和 Reg Log10 入口执行同一任务，类型总览用于对照特殊值和返回宽度。
- [Hlog2](hlog2.md)（`related`）：《Hlog2》说明计算bfloat16_t输入数据以2为底的对数。；《Hlog10》说明计算bfloat16_t输入数据以10为底的对数。。二者在Hlog2的底数、输入宽度和向量宽度可由同dtype的Log/Log10及half/float对应接口直接对照上存在可执行的直接衔接。
- [Log10](../../../../simd_api/basic_api/reg_vector_compute/basic_arithmetic/log10.md)（`related`）：Log10 与《Hlog10》的实质衔接是：Reg Log10 与 bfloat16/half/half2/float 的 log10 入口执行同一以 10 为底的对数任务，区别在执行模型和返回精度。
- [Log10f](../../float_math_functions/log10f.md)（`related`）：Log10f 与《Hlog10》的实质衔接是：Log10f 与 Reg、bfloat16、half 和 half2 的 log10 入口执行同一以 10 为底的对数，区别在执行模型和返回精度。
- [bfloat16类型数学库函数](bfloat16_math_functions.md)（`same_topic`）：Hlog10 与《bfloat16类型数学库函数》的实质衔接是：bfloat16 Hlog10 与 half、float、双 lane 和 Reg Log10 入口执行同一任务，类型总览用于对照特殊值和返回宽度。
<!-- cannbot:related:end -->
