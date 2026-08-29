---
type: API
title: Hrint
description: 获取与输入bfloat16_t数据最接近的整数，若存在两个同样接近的整数则取偶数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hrint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hrint

获取与输入数据最接近的整数，若存在两个同样接近的整数，则获取其中的偶数。
函数原型：bfloat16_t hrint(bfloat16_t x)
返回值：与输入浮点数最接近的整数值。特别场景说明如下：本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
