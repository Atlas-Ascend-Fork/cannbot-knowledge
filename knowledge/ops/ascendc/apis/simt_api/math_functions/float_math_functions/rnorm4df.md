---
type: API
title: Rnorm4df
description: 获取输入数据a、b、c、d的平方和a^2 + b^2 + c^2 + d^2的平方根的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/rnorm4df.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Rnorm4df

功能：获取输入数据a、b、c、d的平方和a^2 + b^2 + c^2 + d^2的平方根的倒数。

函数原型：float rnorm4df(float a, float b, float c, float d)

参数：a（输入）源操作数，b（输入）源操作数，c（输入）源操作数，d（输入）源操作数。

返回值：a^2 + b^2 + c^2 + d^2的平方根的倒数。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，当所有输入均为Subnormal数据时，本接口最终返回nan。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Rnormf](rnormf.md)（`same_topic`）：功能：获取输入数据a、b、c、d的平方和a^2 + b^2 + c^2 + d^2的平方根的倒数。 功能：获取输入数据a中前n个元素的平方和a［0］^2 + a［1］^2 + ...+ a［n-1］^2的平方根的倒数。 相同 reciprocal norm 定义下，固定四标量与地址加可变 n 是可执行的 ABI 和长度选型边界。
<!-- cannbot:related:end -->
