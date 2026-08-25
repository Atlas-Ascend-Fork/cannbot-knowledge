---
type: API
title: 数学函数ynf
description: 获取输入数据x的n阶第二类贝塞尔函数yn的值。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/ynf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 数学函数ynf

功能：获取输入数据x的n阶第二类贝塞尔函数yn的值。

函数原型：float ynf(int n, float x)

参数：n（输入）源操作数，x（输入）源操作数。

返回值：输入数据的第二类贝塞尔函数yn的值。

约束：- n的最大取值为128。 - 针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，在极少数场景下内部计算的除数为Subnormal数据，导致本接口最终结果为±inf。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [数学函数jnf](jnf.md)（`same_topic`）：数学函数jnf 与《数学函数ynf》的实质衔接是：jnf 与 ynf 都接受阶数 n，分别计算第一类和第二类 Bessel 函数；j1f 是 n=1 的直接特化，可核对阶数和 subnormal 限制。
<!-- cannbot:related:end -->
