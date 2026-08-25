---
type: API
title: __hsub
description: 计算两个bfloat16类型数据相减的结果，并遵循CAST_RINT模式对结果进行舍入。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_arithmetic_functions/__hsub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hsub

计算两个bfloat16类型数据相减的结果，并遵循CAST_RINT模式对结果进行舍入。
函数原型：bfloat16_t __hsub(const bfloat16_t x, const bfloat16_t y)
返回值：输入数据相减的结果。本接口不受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hsub](../../half_type/half_arithmetic_functions/_hsub.md)（`same_topic`）：__hsub 与《__hsub》的实质衔接是：__hsub 与 half/bfloat16/half2 的减法入口共享 RINT 差值语义；add/mul/fma 用于区分相邻算术操作而不能作为等价替换。
<!-- cannbot:related:end -->
