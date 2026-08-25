---
type: API
title: __hfmax2
description: 计算输入bfloat16x2_t类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_arithmetic_functions/__hfmax2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hfmax2

功能：计算输入bfloat16x2_t类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。

函数原型：bfloat16x2_t __hfmax2(const bfloat16x2_t x, const bfloat16x2_t y, const bfloat16x2_t z)

参数：x（输入）源操作数，y（输入）源操作数，z（输入）源操作数。

返回值：输入数据各分量乘加的结果。计算的分量a、b、c满足。特殊值：x、y、z任意一个为nan→nan；(x*y为inf,-inf)→nan；(x*y为-inf,inf)→nan；(inf,inf,0)→inf；(inf,-inf,0)→-inf。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hfma](../bfloat16_arithmetic_functions/_hfma.md)（`related`）：焦点处理half/bfloat16 x2 融合乘加与 ReLU 变体；__hfma正文界定“对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理”。候选保持 x2 乘加语义，只改变 half/bfloat16、scalar 或 ReLU 融合形态。
- [__hfma](../../half_type/half_arithmetic_functions/_hfma.md)（`related`）：焦点处理half/bfloat16 x2 融合乘加与 ReLU 变体；__hfma正文界定“对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理”。候选保持 x2 乘加语义，只改变 half/bfloat16、scalar 或 ReLU 融合形态。
- [__hfmax2](../../half_type/half2_arithmetic_functions/_hfmax2.md)（`same_topic`）：焦点处理half/bfloat16 x2 融合乘加与 ReLU 变体；__hfmax2正文界定“计算输入half2类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入”。候选保持 x2 乘加语义，只改变 half/bfloat16、scalar 或 ReLU 融合形态。
- [__hfmax2_relu](_hfmax2_relu.md)（`same_topic`）：焦点处理half/bfloat16 x2 融合乘加与 ReLU 变体；__hfmax2_relu正文界定“计算输入bfloat16x2_t类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。负数结果置为0”。候选保持 x2 乘加语义，只改变 half/bfloat16、scalar 或 ReLU 融合形态。
- [__hfmax2_relu](../../half_type/half2_arithmetic_functions/_hfmax2_relu.md)（`same_topic`）：焦点处理half/bfloat16 x2 融合乘加与 ReLU 变体；__hfmax2_relu正文界定“计算输入half2类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。负数结果置为0”。候选保持 x2 乘加语义，只改变 half/bfloat16、scalar 或 ReLU 融合形态。
<!-- cannbot:related:end -->
