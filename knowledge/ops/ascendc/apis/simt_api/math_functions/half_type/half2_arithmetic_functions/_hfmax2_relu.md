---
type: API
title: __hfmax2_relu
description: 计算输入half2类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_arithmetic_functions/__hfmax2_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hfmax2_relu

功能：计算输入half2类型数据各分量的乘加的结果（前两个输入相乘后与第三个输入相加），并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。

函数原型：half2 __hfmax2_relu(const half2 x, const half2 y, const half2 z)

参数：x（输入）源操作数，y（输入）源操作数，z（输入）源操作数。

返回值：输入数据各分量乘加的结果。本接口受全局饱和寄存器的影响，。特殊值：(任一值为nan,nan)→0；(x*y=±inf,同号inf,nan)→0；(x*y+z为inf,inf)→ASCRT_MAX_NORMAL_FP16；(x*y+z≤0,0)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
