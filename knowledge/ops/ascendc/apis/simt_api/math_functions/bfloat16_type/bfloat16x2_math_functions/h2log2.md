---
type: API
title: H2Log2
description: 获取以2为底，输入数据各元素的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2log2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Log2

功能：获取以2为底，输入数据各元素的对数。

函数原型：bfloat16x2_t h2log2(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：以2为底的输入数据各元素的对数。本接口受全局饱和模式影响，。特殊值：±0→-ASCRT_MAX_NORMAL_BF16；nan→0；inf→ASCRT_MAX_NORMAL_BF16；-inf→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Log10](h2log10.md)（`related`）：H2Log2 提供同一 bfloat16x2 输入的 2 为底对数，且特殊值/饱和模式与 H2Log10 可直接比较。
- [H2Log2](../../half_type/half2_math_functions/h2log2.md)（`same_topic`）：《H2Log2》处理“获取以2为底，输入数据各元素的对数。”。《H2Log2》明确“获取以2为底，输入数据各元素的对数。”，可直接用于核对packed half2 log2 与标量 half/float log2 的同一逐 lane 数学语义。
- [Hlog2](../bfloat16_math_functions/hlog2.md)（`same_topic`）：《Hlog2》说明计算bfloat16_t输入数据以2为底的对数。；《H2Log2》说明获取以2为底，输入数据各元素的对数。。二者在Hlog2的底数、输入宽度和向量宽度可由同dtype的Log/Log10及half/float对应接口直接对照上存在可执行的直接衔接。
- [Hlog2](../../half_type/half_math_functions/hlog2.md)（`same_topic`）：《H2Log2》处理“获取以2为底，输入数据各元素的对数。”。《Hlog2》明确“计算half输入数据以2为底的对数。”，可直接用于核对packed half2 log2 与标量 half/float log2 的同一逐 lane 数学语义。
- [Log2f](../../float_math_functions/log2f.md)（`same_topic`）：《H2Log2》处理“获取以2为底，输入数据各元素的对数。”。《Log2f》明确“获取以2为底输入数据的对数。”，可直接用于核对packed half2 log2 与标量 half/float log2 的同一逐 lane 数学语义。
<!-- cannbot:related:end -->
