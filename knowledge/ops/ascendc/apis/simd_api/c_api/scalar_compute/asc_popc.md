---
type: API
title: asc_popc（标量计算）
description: 获取一个uint64_t类型数字的二进制中1的个数。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_popc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_popc（标量计算）

获取一个uint64_t类型数字的二进制中1的个数。
函数原型：int64_t asc_popc(uint64_t value)
参数：value（输入）：被统计的二进制数字。
返回值：value的二进制中1的个数。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscZeroBitsCnt](asc_zero_bits_cnt.md)（`same_topic`）：AscZeroBitsCnt 与《asc_popc（标量计算）》的实质衔接是：AscZeroBitsCnt 是 64 位零位计数；GetBitCount/popc、前导零和 ffz 提供总位数/零位置的邻近位操作，用于避免把计数与定位混淆。
- [GetBitCount](../../basic_api/scalar_compute/get_bit_count.md)（`same_topic`）：GetBitCount 与《asc_popc（标量计算）》的实质衔接是：GetBitCount 对 countValue=1/0 分别对应 C API 的 asc_popc 与 AscZeroBitsCnt；CountLeadingZero 只统计最高位起连续零，可作为区分“全部位计数”和“前导计数”的直接边界。
- [__popc（整数数学函数）](../../../simt_api/math_functions/integer_math_functions/_popc.md)（`same_topic`）：焦点处理popc 位计数在 SIMT 与 C 标量 API 的等价入口；asc_popc（标量计算）正文说明“获取一个uint64_t类型数字的二进制中1的个数”。候选执行同样的置位比特计数，只改变 API 层和输入位宽。
<!-- cannbot:related:end -->
