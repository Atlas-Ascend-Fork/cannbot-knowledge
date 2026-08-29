---
type: API
title: asc_ffs（标量计算）
description: FindFirstSet接口，输入数据的二进制表示中从最低位向最高位查找第一个值为1的位，并返回其位置，如果没找到则返回-1。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_ffs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_ffs（标量计算）

FindFirstSet接口，输入数据的二进制表示中从最低位向最高位查找第一个值为1的位，并返回其位置，如果没找到则返回-1。
函数原型：int64_t asc_ffs(uint64_t value)
返回值：int64_t类型，输入数据中第一个1出现的位置。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [GetSFFValue](../../basic_api/scalar_compute/get_sff_value.md)（`same_topic`）：FindFirstSet接口，输入数据的二进制表示中从最低位向最高位查找第一个值为1的位，并返回其位置，如果没找到则返回-1。；查找uint64_t类型数值的二进制表示中从最低有效位开始的首个指定比特值（0或1）的位置，如果没找到则返回-1。。两张接口卡共享从低位搜索首个目标 bit 的核心契约，GetSFFValue 将 asc_ffs 的固定查 1 扩展为可指定查 0 或 1。
- [__ffs（整数数学函数）](../../../simt_api/math_functions/integer_math_functions/_ffs.md)（`same_topic`）：FindFirstSet接口，输入数据的二进制表示中从最低位向最高位查找第一个值为1的位，并返回其位置，如果没找到则返回-1。；查找首位 1 的位置。从二进制输入数据的最低位开始，查找第一个值为 1 的比特位的位置并返回其索引（索引从 1 开始计数）；若数据中没有 1，则返回 0。。两张卡都定义从最低位寻找首个 1 的 ffs 操作，但分别采用未命中返回 -1 与返回 0 的契约。
<!-- cannbot:related:end -->
