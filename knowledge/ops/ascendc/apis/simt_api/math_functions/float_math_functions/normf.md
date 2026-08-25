---
type: API
title: Normf
description: 获取输入数据a中前n个元素平方和的平方根。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/normf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Normf

功能：获取输入数据a中前n个元素的平方和a[0]^2 + a[1]^2 +...+ a[n-1]^2的平方根。

函数原型：float normf(int n, float* a)

参数：n（输入）源操作数。输入数据a中连续计算的元素个数，a（输入）源操作数。Unified Buffer、Global Memory或栈空间的地址。

返回值：a[0]^2 + a[1]^2 + ...+ a[n-1]^2的平方根。

约束：- 输入数据a的长度必须大于等于参数n。 - 若n过大，接口性能无法保证。 - 针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，当输入a的所有元素均为Subnormal数据时，会导致接口最终结果为nan。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
