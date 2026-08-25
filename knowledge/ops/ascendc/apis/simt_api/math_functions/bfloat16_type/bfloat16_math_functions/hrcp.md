---
type: API
title: BFloat16数学函数hrcp
description: 获取输入数据x的倒数。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hrcp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BFloat16数学函数hrcp

获取输入数据x的倒数。
函数原型：bfloat16_t hrcp(bfloat16_t x)
返回值：输入数据的倒数。本接口受全局饱和模式影响，特殊值如下：
约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，当输入x为Subnormal数据时，会导致本接口最终结果为±inf。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [H2Rcp](../bfloat16x2_math_functions/h2rcp.md)（`related`）：H2Rcp 是两个 bfloat16 lane 的并行倒数，Hrcp 是标量入口；两者用于按数据是否 packed 选型。
- [Half数学函数hrcp](../../half_type/half_math_functions/hrcp.md)（`related`）：half 与 bfloat16 的 hrcp 都计算倒数，可根据源类型精度和范围选择，不需先转 float。
<!-- cannbot:related:end -->
