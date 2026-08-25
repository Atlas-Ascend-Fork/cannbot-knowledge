---
type: API
title: 数学函数powf
description: 获取输入数据x的y次幂。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/powf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 数学函数powf

功能：获取输入数据x的y次幂。

函数原型：float powf(float x, float y)

参数：x（输入）源操作数，幂计算的底数，y（输入）源操作数，幂计算的指数。

返回值：x的y次幂的结果。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [float类型数学库函数](float_math_functions.md)（`related`）：焦点处理powf 在 float 数学库中的定位；float类型数学库函数正文界定“提供float类型的三角、指数、对数、取整、比较及特殊运算等常用数学库函数列表”。候选总览正文明确列出 powf 并提供其 C99 float 数学函数入口。
<!-- cannbot:related:end -->
