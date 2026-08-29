---
type: API
title: Rhypotf
description: 获取输入数据x、y的平方和x^2 + y^2的平方根的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/rhypotf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Rhypotf

功能：获取输入数据x、y的平方和x^2 + y^2的平方根的倒数。

函数原型：float rhypotf(float x, float y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：x^2 + y^2的平方根的倒数。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，当所有输入均为Subnormal数据时，本接口最终返回nan。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Hypotf](hypotf.md)（`same_topic`）：功能：获取输入数据x、y的平方和x^2 + y^2的平方根的倒数。；功能：获取输入数据x、y的平方和x^2 + y^2的平方根。。候选给出 hypot 值，焦点给出同一量的倒数，两者共享输入与 Subnormal 失效机制，适合在正值与 reciprocal 结果需求之间选择。
<!-- cannbot:related:end -->
