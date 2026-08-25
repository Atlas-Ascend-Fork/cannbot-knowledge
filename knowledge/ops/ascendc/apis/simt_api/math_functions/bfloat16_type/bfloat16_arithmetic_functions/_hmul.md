---
type: API
title: __hmul
description: 计算两个bfloat16类型数据相乘的结果，并遵循CAST_RINT模式对结果进行舍入。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_arithmetic_functions/__hmul.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hmul

计算两个bfloat16类型数据相乘的结果，并遵循CAST_RINT模式对结果进行舍入。
函数原型：bfloat16_t __hmul(const bfloat16_t x, const bfloat16_t y)
返回值：输入数据相乘的结果。本接口不受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hmul](../../half_type/half_arithmetic_functions/_hmul.md)（`related`）：两卡提供相同标量低精度乘法并采用 CAST_RINT，但分别面向 half 与 bfloat16；输入类型和特殊值范围决定入口选择。
- [__hmulx2](../bfloat16x2_arithmetic_functions/_hmulx2.md)（`related`）：__hmul说明计算两个bfloat16类型数据相乘的结果，并遵循CAST_RINT模式对结果进行舍入；对__hmulx2而言，packed half2 乘法应与同名另一 packed 类型和标量 half 乘法按数据宽度选择，不能由相似函数名替代。
<!-- cannbot:related:end -->
