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

<!-- cannbot:related:start -->
## 相关

- [Ascend950 ReduceSum AR 多行归约逐行错](../../../../../runbooks/precision/ascend950_reduce_sum_ar_multibundle_use_per_row.md)（`exemplifies`）：《Ascend950 ReduceSum AR 多行归约逐行错》说明Ascend950 上 ReduceSum<AR> 单次传入 aBundle>1 行时逐行结果错（总量近似但逐元素偏）；改逐行调用 ReduceSum(aBundle=1) 规避。仅当 aBundle>1 才触发。；《AscReduceSum》说明根据mask对源操作数进行归约求和操作，将所有参与计算的元素之和保存到目的操作数。。二者在该故障专指ReduceSum AR一次处理多行时逐行错误，逐行调用、跨chunk累加和归约边界是直接修复/验证点上存在可执行的直接衔接。
- [int32 fp32累加reduce binary_equal不可达](../../../../../runbooks/precision/int32_fp32_reduce_binary_equal.md)（`exemplifies`）：《int32 fp32累加reduce binary_equal不可达》的任务是“int32 输入的 reduce 类算子内部 cast 到 fp32 累加，kernel 的 ReduceSum+bisection cache tree 与 golden 的 pairwise 折半是两棵不同 reduce 树；sum 超过 fp32 精确整数范围 2^24 时舍入路径不同致 1 ULP 差，cast 回 int32 后 bitwise 不一致，binary_equal 永不可达。”。《AscReduceSum》具体提供“根据mask对源操作数进行归约求和操作，将所有参与计算的元素之和保存到目的操作数。”，它直接用于int32→fp32 ReduceSum 的规约树、有效 count 和 2^24 舍入边界。
- [AscPairReduceSum](asc_pair_reduce_sum.md)（`related`）：AscPairReduceSum 只对相邻二元做一次求和并保留半宽结果，常作为归约树中间级；AscReduceSum 则完成全部参与元素到 lane0 的最终归约。
- [AscReduceSumDatablock](asc_reduce_sum_datablock.md)（`related`）：AscReduceSum 对整个 mask 选中集合输出单个和；Datablock 版本对每个 32B 块分别归约并连续输出，适合需要保留块级结果的路径。
- [ReduceSum接口](../../../adv_api/reduction_operations/reduce_sum_interface/reduce_sum_interface.md)（`related`）：Reg C API 在寄存器上完成求和，适合数据已驻留 RegTensor 的路径。
- [ReduceSum](../../../basic_api/memory_vector_compute/reduction_compute/reduce_sum.md)（`same_topic`）：Memory ReduceSum 与 AscReduceSum 都实现求和归约，后者在寄存器 C API 中显式接受 mask；该边对齐同一归约语义的两层接口。
<!-- cannbot:related:end -->
