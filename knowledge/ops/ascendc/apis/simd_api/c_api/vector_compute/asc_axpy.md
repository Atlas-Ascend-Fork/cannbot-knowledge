---
type: API
title: AscAxpy
description: 源操作数src中每个元素与标量value求积后和目的操作数dst中的对应元素相加
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_axpy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscAxpy

源操作数src中每个元素与标量value求积后和目的操作数dst中的对应元素相加计算公式如下：
函数原型：void asc_axpy(__ubuf__ half* dst, __ubuf__ half* src, half value, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [Axpy](../../adv_api/math_compute/axpy_interface/axpy.md)（`related`）：高阶 Axpy 用 Muls+Add 组合并配套临时空间，适合需要高阶 tiling/精度实现的场景。
- [Axpy](../../basic_api/memory_vector_compute/composite_compute/axpy.md)（`related`）：Axpy 与《AscAxpy》的实质衔接是：Axpy 把缩放源加到目的，需与高阶 Axpy、mask/repeat 和临时空间查询配套。
- [AscAxpy](../reg/compound_compute/asc_axpy.md)（`same_topic`）：AscAxpy 与《AscAxpy》的衔接是：AscAxpy 的 C Vector、基础及高阶 Axpy 入口实现同一 alpha*x+y 数据流，差异集中在张量形态、临时空间和调度层级。
<!-- cannbot:related:end -->
