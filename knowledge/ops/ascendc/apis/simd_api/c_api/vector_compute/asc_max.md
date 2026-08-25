---
type: API
title: AscMax
description: 执行逐元素取最大值运算，
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscMax

执行逐元素取最大值运算，计算公式如下：
函数原型：void asc_max(__ubuf__ int16_t* dst, __ubuf__ int16_t* src0, __ubuf__ int16_t* src1, uint32_t count)
约束：dst、src的起始地址需要32字节对齐；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscMaxScalar](asc_max_scalar.md)（`related`）：AscMaxScalar 将第二个 Tensor 改为标量，适合根据广播需求在二元 Tensor Max 与标量 Max 间选型。
- [AscMax](../reg/arithmetic_compute/asc_max.md)（`same_topic`）：AscMax 与《AscMax》的实质衔接是：AscMax 在 Reg 上按 mask 逐 lane 取大；Vector 对应入口、scalar 变体和 AscMin 对照分别界定内存层、操作数形态与相反比较方向。
<!-- cannbot:related:end -->
