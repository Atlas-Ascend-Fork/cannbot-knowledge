---
type: API
title: __hfma_relu
description: 对输入bfloat16类型数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_arithmetic_functions/__hfma_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hfma_relu

对输入bfloat16类型数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。
函数原型：bfloat16_t __hfma_relu(const bfloat16_t x, const bfloat16_t y, const bfloat16_t z)
返回值：x \ y + z的值。本接口不受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hfma_relu](../../half_type/half_arithmetic_functions/_hfma_relu.md)（`same_topic`）：__hfma_relu 与《__hfma_relu》的实质衔接是：__hfma_relu 在 half 上执行 x*y+z 后 ReLU；基础 hfma 与 bfloat16 对应入口拆分类型，两个历史命名为 hfmax2_relu 的卡正文同样是 packed FMA+ReLU 契约。
- [__hfmax2_relu](../bfloat16x2_arithmetic_functions/_hfmax2_relu.md)（`same_topic`）：focal 正文实际描述三输入乘加后 ReLU，与 bfloat16 的 __hfma_relu 语义一致；该边揭示标题与正文不一致时的真实契约桥。
<!-- cannbot:related:end -->
