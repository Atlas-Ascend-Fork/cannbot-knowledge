---
type: Optimization
title: 逐样本标量累加改片上向量缓冲 + 循环外归约
description: 把逐样本标量累加改为每样本结果写片上向量缓冲槽位，循环结束后一次向量归约。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/per_sample_scalar_accum_onchip_vector.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：逐样本标量累加改片上向量缓冲 + 循环外归约

单一优化点

## 1. 原理
逐样本循环中把每样本结果以标量累加到一个 accumulator（每样本一次"vector→scalar 同步读结果 + 标量加"），样本数大时同步累积。改为：每样本结果写入片上向量缓冲的一个槽位，循环结束后对该向量缓冲做一次向量归约。消除逐样本标量同步。

## 2. 性能问题模式
- 算子逐样本循环，每样本产出一个标量结果并累加到单个 accumulator。
- 每样本都有"读结果（跨流水线同步）+ 标量累加"。
- N' 大时同步开销累积。

## 3. 正确性红线
- 片上向量缓冲须覆盖本核处理的样本数（或分块覆盖，分块归约后合并）。
- 向量归约顺序与原标量累加在浮点误差范围内等价（归约为加法，结合律下等价，误差可接受）。
- 尾块/对齐：缓冲槽位对齐，尾样本 fallback。
- reduction=mean 时累加计数（有效样本数）同样用向量缓冲 + 归约，不得标量化。

## 4. 泛化条件
- 逐样本循环累加标量的归约算子（reduction=mean/sum）。
- 片上缓冲可容纳每核样本数的标量（或可分块）。
- 不适用：样本数极大且无法分块（缓冲不足）；累加非线性（非加法）。

## 5. 实施步骤
1. 把 accumulator 标量改为片上向量缓冲（槽位数 = 本核样本数，分块则 = 块大小）。
2. 每样本结果 SetValue 到缓冲[slot]（vector 写，无跨流水线同步）。
3. 循环外对缓冲做一次向量归约（WholeReduce 类）。
4. 超大样本数时分块：每块填满缓冲 → 归约到 accumulator → 下一块。
5. mean 模式计数同理。
6. 精度 + 性能复测。

## 6. LLM 前置问题
- 算子是否逐样本标量累加？累加是否为加法（可向量归约）？
- 本核样本数能否被片上缓冲容纳（或分块）？
- 是否 mean 模式需同时累加计数？

## 7. 验收标准
- 编译通过。
- 精度在算子阈值内（归约等价）。
- 大 N' 的 mean/sum case 性能提升。

## 检索卡（短卡）

动作：把逐样本标量累加改为每样本结果写片上向量缓冲槽位，循环结束后一次向量归约。
适用：逐样本循环累加标量的归约算子（reduction=mean/sum）；片上缓冲可容纳每核样本数或可分块；累加为加法。
限制：向量归约与原标量累加须浮点误差内等价；尾块对齐 fallback；mean 模式计数同样向量归约不得标量化。
范围：reduction=mean/sum 类算子的逐样本累加环节。
检索词：SetValue、WholeReduce、向量缓冲、分块归约、vector→scalar 同步、accumulator。
机会：每样本一次读结果跨流水线同步+标量累加，样本数大时同步开销累积。
