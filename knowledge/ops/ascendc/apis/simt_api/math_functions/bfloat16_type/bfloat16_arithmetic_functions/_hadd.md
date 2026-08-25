---
type: API
title: __hadd
description: 计算两个bfloat16类型数据相加的结果，并遵循CAST_RINT模式对结果进行舍入。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_arithmetic_functions/__hadd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hadd

计算两个bfloat16类型数据相加的结果，并遵循CAST_RINT模式对结果进行舍入。
函数原型：bfloat16_t __hadd(const bfloat16_t x, const bfloat16_t y)
返回值：输入数据相加的结果。本接口不受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__haddx2](../bfloat16x2_arithmetic_functions/_haddx2.md)（`related`）：“__haddx2”处理计算两个bfloat16x2_t类型数据各分量的相加结果，并遵循CAST_RINT模式对结果进行舍入。；“__hadd”明确计算两个bfloat16类型数据相加的结果，并遵循CAST_RINT模式对结果进行舍入。。实质衔接：bfloat16x2 加法与标量 bfloat16 加法区分向量宽度，half2 版本保持 x2 操作不变而改变数据类型。
- [__hadd](../../half_type/half_arithmetic_functions/_hadd.md)（`same_topic`）：__hadd 与《__hadd》的实质衔接是：__hadd 与 half/bfloat16/half2 的加法入口共享加法与 RINT 语义；sub、mul、fma 用于区分运算符而避免把算术族名称当作等价替换。
<!-- cannbot:related:end -->
