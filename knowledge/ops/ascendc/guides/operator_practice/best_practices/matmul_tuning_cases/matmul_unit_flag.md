---
type: Guide
title: Matmul高阶API开启UnitFlag
description: 开启UnitFlag为MMAD与FIXPIPE提供512B细粒度同步，实现计算与搬出流水并行，提升算子性能。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_unit_flag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Matmul高阶API开启UnitFlag

## 案例介绍
本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，开启UnitFlag功能对算子性能的提升效果。UnitFlag功能为AIC核中MMAD计算指令和FIXPIPE数据搬运指令提供了基于内存访问的细粒度同步，使计算与搬运流水并行。开启UnitFlag功能的方式为将MatmulConfig中的enUnitFlag参数设置为true。enUnitFlag参数的详细介绍请参考MatmulConfig。
-   开启UnitFlag的适用场景
算子的MMAD流水和FIXPIPE流水之间串行执行，FIXPIPE等待MMAD计算完成才搬出结果，这个指令同步等待的时间在算子整体执行耗时中占比较高。这种场景可以开启UnitFlag功能，以获得MMAD和FIXPIPE流水并行的性能收益。如果算子原本的MMAD、FIXPIPE流水可以被其他流水掩盖（比如MTE2 Bound），这时开启UnitFlag功能总体收益很小。
-   开启UnitFlag的约束条件
-   UnitFlag功能仅支持Norm、IBShare、MDL三个模板。
-   开启UnitFlag功能时，不支持算子内同时存在L0C Buffer（CO1）搬出到Global Memory和L1 Buffer（A1）搬出到Global Memory的两种流水。
-   开启UnitFlag功能时，若同时开启L0C累加功能，不支持多次Iterate计算、一次GetTensorC输出。
本案例的算子规格如下：
算子规格
当前案例使用的AI处理器共20个核，每个核包含1个AIC核和2个AIV核。
算子的Tiling参数如下：
-   原始shape：M=128, N=30720, K=64。
-   单核shape：按20个AIC核进行切分，singleCoreM=128，singleCoreN=1536，singleCoreK=64。
对于B矩阵，沿着N轴进行切分，切分成20份singleCoreN，单核上处理K * SingleCoreN大小的数据。对于A矩阵，M轴不进行切分即singleCoreM=M，单核上处理singleCoreM * K大小的数据。总共20个核参与计算。
-   基本块shape：baseM=128，baseN=256，baseK=64。
-   L1相关Tiling参数：stepM=1，stepN=1，stepKa=4，stepKb=4，depthA1=8，depthB1=8。
## 获取性能数据
使用msOpProf工具获取算子仿真流水图和上板Profiling数据。因为UnitFlag功能主要优化MMAD和FIXPIPE流水串行问题，所以获取性能数据后重点分析Cube、FIXPIPE的流水情况。
## 分析主要瓶颈点
-   优化前的流水图如下。如下图中红框所示，每一轮MMAD计算流水和FIXPIPE数据搬出流水之间都是串行执行的，完成MMAD计算后才开始FIXPIPE数据搬出，考虑实现MMAD与FIXPIPE之间流水并行来优化算子性能。
