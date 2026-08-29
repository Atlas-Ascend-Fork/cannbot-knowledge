---
type: API
title: asc_clz（标量计算）
description: 计算一个uint64_t类型整数在二进制表示下的前导零个数，即从二进制最高位开始，到第一个出现二进制1为止，中间连续的0的数量。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_clz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_clz（标量计算）

计算一个uint64_t类型整数在二进制表示下的前导零个数，即从二进制最高位开始，到第一个出现二进制1为止，中间连续的0的数量。
函数原型：int64_t asc_clz(uint64_t value_in)
返回值：反馈value_in的前导0的个数。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [CountLeadingZero](../../basic_api/scalar_compute/count_leading_zero.md)（`same_topic`）：计算一个uint64_t类型整数在二进制表示下的前导零个数；统计uint64_t类型数值的二进制表示中前导0的个数（二进制表示中最高有效位到第一个'1'的'0'的数量，输入为0时返回64）。。两页提供同一 uint64 前导零计数语义，分别是 C API 标量入口与基础 API 入口。
- [__clz（整数数学函数）](../../../simt_api/math_functions/integer_math_functions/_clz.md)（`same_topic`）：计算一个uint64_t类型整数在二进制表示下的前导零个数；前导零计数函数。从输入数据的二进制最高有效位开始，返回连续的前导零的位数。。asc_clz 与 SIMT __clz 都从最高有效位计算连续零数，但执行模型和参数重载不同，关系可帮助按 Scalar/SIMT 路线选型。
<!-- cannbot:related:end -->
