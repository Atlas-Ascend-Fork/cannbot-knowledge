---
type: API
title: __hfma
description: 对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_arithmetic_functions/__hfma.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hfma

对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理。
函数原型：bfloat16_t __hfma(bfloat16_t x, bfloat16_t y, bfloat16_t z)
返回值：x \ y+ z的值。本接口不受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hfmax2](../bfloat16x2_arithmetic_functions/_hfmax2.md)（`related`）：焦点处理half/bfloat16 x2 融合乘加与 ReLU 变体；__hfma正文界定“对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理”。候选保持 x2 乘加语义，只改变 half/bfloat16、scalar 或 ReLU 融合形态。
- [__hfma](../../half_type/half_arithmetic_functions/_hfma.md)（`same_topic`）：bfloat16 版本完成同一融合乘加，源精度不同。
- [__hfma_relu](../../half_type/half_arithmetic_functions/_hfma_relu.md)（`same_topic`）：__hfma_relu 与《__hfma》的实质衔接是：__hfma_relu 在 half 上执行 x*y+z 后 ReLU；基础 hfma 与 bfloat16 对应入口拆分类型，两个历史命名为 hfmax2_relu 的卡正文同样是 packed FMA+ReLU 契约。
<!-- cannbot:related:end -->
