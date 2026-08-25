---
type: API
title: AscReduceSumDatablock
description: 根据mask将每个DataBlock中参与计算的元素相加，结果依次保存在目的操作数最低位。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reduce_compute/asc_reduce_sum_datablock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscReduceSumDatablock

根据mask将每个DataBlock（32B）中参与计算的元素相加，并将最终的计算结果依次保存在dst的最低位。
约束：指令内累加顺序采用二叉树累加方式，在每个DataBlock（32B）内两两相加逐层归约求和，结果连续写入到目的操作数，目的操作数中的其它元素置0。；当DataBlock中的元素均不参与计算（mask全为0）时，将0写入dst对应位置（对于浮点数则为+0）。；对于输入为uint16_t/int16_t类型的情况，会提升精度到uint32_t/int32_t进行计算。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
