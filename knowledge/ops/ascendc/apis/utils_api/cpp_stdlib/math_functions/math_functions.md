---
type: API
title: 数学函数
description: 提供abs、ceil_div、sqrt等数学工具函数。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/math_functions/math_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数学函数

提供标量数学工具函数，包含 abs、ceil_div 和 sqrt。abs 取输入数据的绝对值，支持 int8_t、int16_t、int32_t、float、int64_t；ceil_div 计算两个整数相除后向上取整的结果，可在 Host 侧与 AI Core 侧使用；sqrt 计算输入数据的平方根，支持 float 和 int64_t。
约束：ceil_div 的 T、U 必须为整型，b 为 0 时结果为 0，有符号输入需保证 a≥0 且 b>0；sqrt 输入必须为非负数，int64_t 类型结果会被截断为整数。abs 和 sqrt 当前仅 Ascend 950PR/Ascend 950DT 支持。
