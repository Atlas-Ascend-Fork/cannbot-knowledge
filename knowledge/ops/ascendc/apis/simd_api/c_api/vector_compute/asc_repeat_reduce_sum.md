---
type: API
title: AscRepeatReduceSum
description: 对每个 Repeat 内的元素按二叉树方式求和；half 累加中间结果超过 65504 时按 65504 保存。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_repeat_reduce_sum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# AscRepeatReduceSum

对每个Repeat内所有元素求和。 源操作数相加采用二叉树的方式，两两相加。以256个half类型数据求和为例，每个Repeat可以计算128个half类型数据，分成2个Repeat计算；每个Repeat内，通过二叉树的方式，两两相加。 需要注意的是，两两相加计算过程中，计算结果大于65504时结果保存为65504。例如，源操作数为[60000,60000,-30000,100]，首先60000+60000溢出，结果为65504，然后计算-30000+100=-29900，最后计算65504-29900=35604。
函数原型：void asc_repeat_reduce_sum(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst的起始地址，输入类型为half时需要2字节对齐，输入类型为float时需要4字节对齐。；src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
