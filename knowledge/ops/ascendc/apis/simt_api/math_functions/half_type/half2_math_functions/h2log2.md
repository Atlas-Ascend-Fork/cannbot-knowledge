---
type: API
title: H2Log2
description: 获取以2为底，输入数据各元素的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2log2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Log2

功能：获取以2为底，输入数据各元素的对数。

函数原型：half2 h2log2(half2 x)

参数：x（输入）源操作数。

返回值：以2为底的输入数据各元素的对数。本接口受全局饱和寄存器影响，。特殊值：±0→-ASCRT_MAX_NORMAL_FP16；inf→ASCRT_MAX_NORMAL_FP16；nan→0；-inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Log](h2log.md)（`same_topic`）：H2Log：H2Log、H2Log2、H2Log10分别计算e/2/10底对数，bfloat16x2同名接口提供类型变体；这些关系直接防止底数或数据类型选错。 目标卡《H2Log2》补充：获取以2为底，输入数据各元素的对数。
- [H2Log10](h2log10.md)（`same_topic`）：H2Log2 补充以 2 为底的同 dtype 双分量对数路径。
- [H2Log2](../../bfloat16_type/bfloat16x2_math_functions/h2log2.md)（`same_topic`）：《H2Log2》处理“获取以2为底，输入数据各元素的对数。”。《H2Log2》明确“获取以2为底，输入数据各元素的对数。”，可直接用于核对packed half2 log2 与标量 half/float log2 的同一逐 lane 数学语义。
- [Hlog2](../../bfloat16_type/bfloat16_math_functions/hlog2.md)（`same_topic`）：Hlog2说明计算bfloat16_t输入数据以2为底的对数。
- [Hlog2](../half_math_functions/hlog2.md)（`same_topic`）：Hlog2 与《H2Log2》的实质衔接是：Hlog2 与 log/log10、packed/float Log2 和 half 数学库共同定义二进制对数。
- [Log2f](../../float_math_functions/log2f.md)（`same_topic`）：Log2f说明获取以2为底输入数据的对数。
<!-- cannbot:related:end -->
