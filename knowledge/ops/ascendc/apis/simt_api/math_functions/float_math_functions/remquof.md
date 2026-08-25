---
type: API
title: Remquof
description: 获取输入数据x除以y的余数r。r=x-ny，其中n是x除以y的商，n取最接近x除以y浮点数结果的整数，当x除以y的浮点数结果与左右最接近的整数距离相等时，商取偶数，同时将商赋值给指针变量quo。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/remquof.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Remquof

功能：获取输入数据x除以y的余数r。r=x-ny，其中n是x除以y的商，n取最接近x除以y浮点数结果的整数，当x除以y的浮点数结果与左右最接近的整数距离相等时，商取偶数，同时将商赋值给指针变量quo。

函数原型：float remquof(float x, float y, int *quo)

参数：x（输入）源操作数，y（输入）源操作数，quo（输出）Unified Buffer、Global Memory或栈空间的地址，用于存储除法运算的商。

返回值：输入数据x除以y的余数。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
