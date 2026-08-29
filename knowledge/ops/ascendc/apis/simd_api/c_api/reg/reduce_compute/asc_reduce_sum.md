---
type: API
title: AscReduceSum
description: 根据mask对源操作数进行归约求和操作，将所有参与计算的元素之和保存到目的操作数。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reduce_compute/asc_reduce_sum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscReduceSum

根据mask对源操作数src进行归约求和操作，用于将src中的所有参与计算的元素求和，得到的结果保存在dst中的0位置。
约束：指令内累加顺序采用二叉树累加方式，结果连续写入到目的操作数，目的操作数中的其它元素置0。；当所有元素均不参与计算（mask全为0）时，将0写入目的操作数对应位置（特别的，对于浮点数为+0）。；对于输入为uint16_t/int16_t类型的情况，会提升精度到uint32_t/int32_t进行计算。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
