---
type: API
title: __hfmax2_relu
description: 计算输入bfloat16x2_t类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_arithmetic_functions/__hfmax2_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hfmax2_relu

功能：计算输入bfloat16x2_t类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。

函数原型：bfloat16x2_t __hfmax2_relu(const bfloat16x2_t x, const bfloat16x2_t y, const bfloat16x2_t z)

参数：x（输入）源操作数，y（输入）源操作数，z（输入）源操作数。

返回值：输入数据各分量乘加的结果。计算的分量a、b、c满足。特殊值：x、y、z任意一个为nan→nan；(inf,inf,-inf)→nan；(-inf,-inf,inf)→inf；(inf,inf,0)→inf。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hfmax2](../../half_type/half2_arithmetic_functions/_hfmax2.md)（`related`）：《__hfmax2》的任务是“计算输入half2类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。”。《__hfmax2_relu》具体提供“计算输入bfloat16x2_t类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。”，它直接用于三输入 FMA 舍入、融合 ReLU 及 bfloat16x2 对应合同。
- [__hfmax2_relu](../../half_type/half2_arithmetic_functions/_hfmax2_relu.md)（`related`）：half2 同名接口提供相同的双分量运算与 ReLU 后处理，但输入数据类型不同。
- [__hfma_relu](../bfloat16_arithmetic_functions/_hfma_relu.md)（`same_topic`）：focal 正文实际描述三输入乘加后 ReLU，与 bfloat16 的 __hfma_relu 语义一致；该边揭示标题与正文不一致时的真实契约桥。
- [__hfma_relu](../../half_type/half_arithmetic_functions/_hfma_relu.md)（`same_topic`）：__hfma_relu 与《__hfmax2_relu》的实质衔接是：__hfma_relu 在 half 上执行 x*y+z 后 ReLU；基础 hfma 与 bfloat16 对应入口拆分类型，两个历史命名为 hfmax2_relu 的卡正文同样是 packed FMA+ReLU 契约。
- [__hfmax2](_hfmax2.md)（`same_topic`）：焦点处理half/bfloat16 x2 融合乘加与 ReLU 变体；__hfmax2_relu正文界定“计算输入bfloat16x2_t类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。负数结果置为0”。候选保持 x2 乘加语义，只改变 half/bfloat16、scalar 或 ReLU 融合形态。
<!-- cannbot:related:end -->
