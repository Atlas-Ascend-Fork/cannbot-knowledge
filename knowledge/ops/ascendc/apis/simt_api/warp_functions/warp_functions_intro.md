---
type: API
title: Warp函数
description: Warp是SIMT线程执行和调度的基本单位。一个线程块内的线程会按照线性线程号被划分为多个Warp，当前一个Warp包含32个线程。同一Warp内的线程执行相同的指令流，但每个线程拥有独立的寄存器和Lane
  ID，可处理不同的数据地址和分支路径。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_functions_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Warp函数

Warp 是 SIMT 线程执行和调度的基本单位，一个 Warp 包含 32 个线程，执行相同指令流但拥有独立寄存器和 Lane ID。Warp 函数用于 Warp 内轻量级线程协作，直接在 Warp 内完成寄存器级通信，适合小范围低开销协作场景。

基本概念：Lane 为 Warp 内单个线程执行位置，Lane ID 取值 [0,31]；活跃线程为当前指令路径上实际参与执行的线程；分支发散时未进入当前路径的线程为非活跃状态。

Warp 函数分类：Warp Vote 类（条件值汇总，全真/任意为真/位图/活跃掩码）、Warp Shfl 类（按 Lane ID 交换寄存器数据，邻近通信/扫描/归约）、Warp Reduce 类（求和/最大值/最小值归约）、Lane ID 类（获取 Lane ID 或生成 Lane Mask）。

使用建议：Warp 函数仅在当前 Warp 内生效，不能跨 Warp 或跨 Block 同步；面向活跃线程执行，分支发散时需确认参与计算的 Lane 集合；Shfl 读取非活跃 Lane 可能得到未初始化值；Reduce 适合 Warp 内小范围归约，跨 Warp 需结合 UB/同步/原子操作；Warp 函数不等价于内存栅栏。仅 Ascend 950PR/950DT 支持。
