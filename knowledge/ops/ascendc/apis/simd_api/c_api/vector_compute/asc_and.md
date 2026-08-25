---
type: API
title: AscAnd
description: asc_and（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_and.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscAnd

执行矢量与运算。计算公式如下：
函数原型：void asc_and(__ubuf__ int16_t* dst, __ubuf__ int16_t* src0, __ubuf__ int16_t* src1, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src0、src1的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [And](../../basic_api/memory_vector_compute/logical_compute/and.md)（`same_topic`）：AscAnd：C Vector AscAnd、C Reg AscAnd及两套基础And都是逐元素按位与，关系用于核对操作数容器、mask与数据类型约束。 目标卡《And》补充：对LocalTensor中的元素做按位与运算，支持整个tensor、前n个数据连续计算和高维切分计算三种调用方式。
- [And](../../basic_api/reg_vector_compute/logical_compute/and.md)（`same_topic`）：AscAnd：C Vector AscAnd、C Reg AscAnd及两套基础And都是逐元素按位与，关系用于核对操作数容器、mask与数据类型约束。 目标卡《And》补充：根据mask对两个RegTensor或MaskReg执行按位与操作，将结果写入目的操作数，支持ZEROING模式。
- [AscAnd](../reg/logic_compute/asc_and.md)（`same_topic`）：AscAnd：C Vector AscAnd、C Reg AscAnd及两套基础And都是逐元素按位与，关系用于核对操作数容器、mask与数据类型约束。 目标卡《AscAnd》补充：根据mask对源操作数src0、src1执行按位与操作，结果写入dst，支持矢量数据寄存器和掩码寄存器。
<!-- cannbot:related:end -->
