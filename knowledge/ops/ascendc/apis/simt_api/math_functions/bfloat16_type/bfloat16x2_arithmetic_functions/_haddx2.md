---
type: API
title: __haddx2
description: 计算两个bfloat16x2_t类型数据各分量的相加结果，并遵循CAST_RINT模式对结果进行舍入。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_arithmetic_functions/__haddx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __haddx2

功能：计算两个bfloat16x2_t类型数据各分量的相加结果，并遵循CAST_RINT模式对结果进行舍入。

函数原型：bfloat16x2_t __haddx2(const bfloat16x2_t x, const bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量相加的结果。相加的分量x和y满足。特殊值：±0→±0；inf→inf；-inf→-inf；inf→nan；-inf→nan；对有限值x（包括±0），x=-y→0；ASCRT_MAX_NORMAL_BF16→inf。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hadd](../bfloat16_arithmetic_functions/_hadd.md)（`related`）：“__haddx2”处理计算两个bfloat16x2_t类型数据各分量的相加结果，并遵循CAST_RINT模式对结果进行舍入。；“__hadd”明确计算两个bfloat16类型数据相加的结果，并遵循CAST_RINT模式对结果进行舍入。。实质衔接：bfloat16x2 加法与标量 bfloat16 加法区分向量宽度，half2 版本保持 x2 操作不变而改变数据类型。
- [__haddx2](../../half_type/half2_arithmetic_functions/_haddx2.md)（`related`）：“__haddx2”处理计算两个bfloat16x2_t类型数据各分量的相加结果，并遵循CAST_RINT模式对结果进行舍入。；“__haddx2”明确计算两个half2类型数据各分量的相加结果，并遵循CAST_RINT模式对结果进行舍入。。实质衔接：bfloat16x2 加法与标量 bfloat16 加法区分向量宽度，half2 版本保持 x2 操作不变而改变数据类型。
- [__hadd](../../half_type/half_arithmetic_functions/_hadd.md)（`same_topic`）：__hadd 与《__haddx2》的实质衔接是：__hadd 与 half/bfloat16/half2 的加法入口共享加法与 RINT 语义；sub、mul、fma 用于区分运算符而避免把算术族名称当作等价替换。
<!-- cannbot:related:end -->
