---
type: API
title: Hlog2
description: 计算bfloat16_t输入数据以2为底的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hlog2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hlog2

获取以2为底，输入数据的对数。
函数原型：bfloat16_t hlog2(bfloat16_t x)
返回值：以2为底的x的对数。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [BFloat16数学函数hlog](hlog.md)（`related`）：《Hlog2》说明计算bfloat16_t输入数据以2为底的对数。；《BFloat16数学函数hlog》说明获取以e为底，输入数据的对数。。二者在Hlog2的底数、输入宽度和向量宽度可由同dtype的Log/Log10及half/float对应接口直接对照上存在可执行的直接衔接。
- [Hlog10](hlog10.md)（`related`）：《Hlog2》说明计算bfloat16_t输入数据以2为底的对数。；《Hlog10》说明计算bfloat16_t输入数据以10为底的对数。。二者在Hlog2的底数、输入宽度和向量宽度可由同dtype的Log/Log10及half/float对应接口直接对照上存在可执行的直接衔接。
- [Hlog2](../../half_type/half_math_functions/hlog2.md)（`related`）：Hlog2 与《Hlog2》的实质衔接是：Hlog2 与 log/log10、packed/float Log2 和 half 数学库共同定义二进制对数。
- [Log2f](../../float_math_functions/log2f.md)（`related`）：《Hlog2》说明计算bfloat16_t输入数据以2为底的对数。；《Log2f》说明获取以2为底输入数据的对数。。二者在Hlog2的底数、输入宽度和向量宽度可由同dtype的Log/Log10及half/float对应接口直接对照上存在可执行的直接衔接。
- [H2Log2](../bfloat16x2_math_functions/h2log2.md)（`same_topic`）：《Hlog2》说明计算bfloat16_t输入数据以2为底的对数。；《H2Log2》说明获取以2为底，输入数据各元素的对数。。二者在Hlog2的底数、输入宽度和向量宽度可由同dtype的Log/Log10及half/float对应接口直接对照上存在可执行的直接衔接。
- [H2Log2](../../half_type/half2_math_functions/h2log2.md)（`same_topic`）：Hlog2说明计算bfloat16_t输入数据以2为底的对数。
<!-- cannbot:related:end -->
