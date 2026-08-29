---
type: Guide
title: SIMT算子优化概述
description: SIMT编程模式以线程（Thread）为基本编程单位，由开发者编写单个线程的执行逻辑，再通过>>配置将大量线程组织为线程块（线程块）与线程网格（Grid），调度到硬件的Vector
  Core（物理核，即AIV核）上以Warp为单位并行执行。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simt_operator_optimization/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 概述

## 整体性能优化策略
SIMT编程模式以线程（Thread）为基本编程单位，由开发者编写单个线程的执行逻辑，再通过>>配置将大量线程组织为线程块（线程块）与线程网格（Grid），调度到硬件的Vector Core（物理核，即AIV核）上以Warp为单位并行执行。
性能优化的整体目标是让算子在硬件上尽可能高效地运行，核心在于保持各类硬件资源处于忙碌且有效的状态。SIMT算子的优化主要围绕以下三个基本策略展开：
- 最大化利用率（Maximize Utilization）：让尽可能多的物理核、线程并行工作，使硬件的并行计算能力被充分发挥，避免物理核闲置或线程排队等待。
- 最大化存储吞吐量（Maximize Memory Throughput）：尽量减少低带宽的数据搬运，让每一次Global Memory（GM）访问都搬运尽可能多的有效数据，充分利用GM带宽、Cache和Unified Buffer（UB）。
- 最大化指令吞吐量（Maximize Instruction Throughput）：减少线程内高开销指令、冗余计算和分支发散，提升计算指令的有效执行占比。
这三种策略对算子性能的影响程度因算子而异，应结合实测性能数据确定主要瓶颈后再针对性优化。优化的一般流程是：先建立理论性能基准（理论读写数据量、GM理论带宽），再使用msOpProf等工具采集实际性能数据（Task Duration、GM读写带宽、DCache访问次数、aiv_vec_ratio等），对比理论与实测的差距定位瓶颈，最后从对应层次选择优化手段并通过性能数据验证优化效果。下面分别介绍三个层次的优化方法。
## 最大化利用率
最大化利用率的目标是充分发挥硬件并行能力。SIMT算子的利用率优化可以从应用级、设备级和物理核级三个层面理解：应用级关注核函数启动配置是否让足够多的物理核并行工作；设备级与物理核级关注单个物理核内的线程、Warp是否能保持忙碌，避免因资源限制（如寄存器）导致并行度下降。在Ascend C SIMT中，主要通过核函数的执行配置（gridDim、blockDim、__launch_bounds__）实现物理核资源的并行优化。
- 合理配置线程块数量，平衡并行核数与调度开销
线程块最终被调度到物理核上执行，一个物理核同一时刻只能驻留并执行一个线程块。线程块数量过少会导致物理核闲置、并行度不足、单核工作量过重；线程块数量远超物理核数时，超出部分需排队等待前序线程块执行完成，多线程块的启动和调度固定开销会明显累积。因此线程块数量应结合物理核数与数据规模设置。
- 合理配置最大线程数，避免寄存器溢出降低有效利用率
核函数通过__launch_bounds__指定的最大线程数决定每个线程可用的寄存器数量：最大线程数越大，每个线程可分配的寄存器越少。对于计算密集型算子，若线程数配置过高导致每个线程的寄存器数量不足，中间数据会溢出到位于Global Memory的栈空间，引入额外的GM访问，反而降低有效利用率。应先通过--cce-res-usage编译选项查看寄存器使用情况（Stack size大于0即表明溢出），再根据寄存器与最大线程数的对应关系选择一档能满足单线程寄存器需求的最大线程数。
