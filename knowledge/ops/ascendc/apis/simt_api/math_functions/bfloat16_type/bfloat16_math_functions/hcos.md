---
type: API
title: BFloat16数学函数hcos
description: 获取输入数据的三角函数余弦值。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hcos.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BFloat16数学函数hcos

获取输入数据的三角函数余弦值。
函数原型：bfloat16_t hcos(bfloat16_t x)
返回值：输入数据的三角函数余弦值。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Half数学函数hcos](../../half_type/half_math_functions/hcos.md)（`related`）：BFloat16数学函数hcos 与《Half数学函数hcos》的实质衔接是：bfloat16 hcos 与同类型 hsin 共享输入输出宽度，half hcos 提供相同余弦任务的另一精度契约。
- [BFloat16数学函数hsin](hsin.md)（`same_topic`）：BFloat16数学函数hcos 与《BFloat16数学函数hsin》的实质衔接是：bfloat16 hcos 与同类型 hsin 共享输入输出宽度，half hcos 提供相同余弦任务的另一精度契约。
<!-- cannbot:related:end -->
