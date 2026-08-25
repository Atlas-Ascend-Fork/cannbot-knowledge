---
type: API
title: __hfmax2
description: 计算输入half2类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_arithmetic_functions/__hfmax2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hfmax2

功能：计算输入half2类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。

函数原型：half2 __hfmax2(const half2 x, const half2 y, const half2 z)

参数：x（输入）源操作数，y（输入）源操作数，z（输入）源操作数。

返回值：输入数据各分量乘加的结果。本接口受全局饱和寄存器的影响，。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hfmax2_relu](../../bfloat16_type/bfloat16x2_arithmetic_functions/_hfmax2_relu.md)（`related`）：《__hfmax2》的任务是“计算输入half2类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。”。《__hfmax2_relu》具体提供“计算输入bfloat16x2_t类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。”，它直接用于三输入 FMA 舍入、融合 ReLU 及 bfloat16x2 对应合同。
- [__hfmax2](../../bfloat16_type/bfloat16x2_arithmetic_functions/_hfmax2.md)（`same_topic`）：焦点处理half/bfloat16 x2 融合乘加与 ReLU 变体；__hfmax2正文界定“计算输入half2类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入”。候选保持 x2 乘加语义，只改变 half/bfloat16、scalar 或 ReLU 融合形态。
- [__hfmax2_relu](_hfmax2_relu.md)（`same_topic`）：《__hfmax2》的任务是“计算输入half2类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。”。《__hfmax2_relu》具体提供“计算输入half2类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。”，它直接用于三输入 FMA 舍入、融合 ReLU 及 bfloat16x2 对应合同。
<!-- cannbot:related:end -->
