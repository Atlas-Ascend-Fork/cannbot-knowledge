---
type: API
title: Sincospif
description: 获取输入数据与π相乘的三角函数正弦值和余弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/sincospif.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Sincospif

功能：获取输入数据与π相乘的三角函数正弦值和余弦值。

函数原型：void sincospif(float x, float *s, float *c)

参数：x（输入）源操作数，s（输出）Unified Buffer、Global Memory或栈空间的地址，用于存储输入数据与π相乘的三角函数正弦值，c（输出）Unified Buffer、Global Memory或栈空间的地址，用于存储输入数据与π相乘的三角函数余弦值。

返回值：当x*π超出float最大范围或超出float最小范围时，输出值为nan；当输入x为inf、-inf、nan时，输出值为nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Sincosf](sincosf.md)（`same_topic`）：获取输入数据与π相乘的三角函数正弦值和余弦值；获取输入数据的三角函数正弦值和余弦值。两端一次返回 sin/cos 双结果，区别是 Sincospif 先把输入按 π 缩放而 Sincosf 直接使用弧度；对照可避免调用者重复乘 π 或漏乘 π。
<!-- cannbot:related:end -->
