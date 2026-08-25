---
type: API
title: BFloat16数学函数hlog
description: 获取以e为底，输入数据的对数。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hlog.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BFloat16数学函数hlog

获取以e为底，输入数据的对数。
函数原型：bfloat16_t hlog(bfloat16_t x)
返回值：以e为底的x的对数。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Half数学函数hlog](../../half_type/half_math_functions/hlog.md)（`related`）：bfloat16 Hlog 与 half Hlog 数学语义相同但精度和特殊值范围不同，可用于 dtype 路径迁移。
- [Hlog10](hlog10.md)（`related`）：Hlog10 补充十进制对数，与自然对数 Hlog 共同覆盖常用底数转换。
- [Hlog2](hlog2.md)（`related`）：《Hlog2》说明计算bfloat16_t输入数据以2为底的对数。；《BFloat16数学函数hlog》说明获取以e为底，输入数据的对数。。二者在Hlog2的底数、输入宽度和向量宽度可由同dtype的Log/Log10及half/float对应接口直接对照上存在可执行的直接衔接。
<!-- cannbot:related:end -->
