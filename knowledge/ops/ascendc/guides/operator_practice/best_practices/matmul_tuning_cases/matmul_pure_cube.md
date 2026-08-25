---
type: Guide
title: Matmul高阶API开启纯Cube模式
description: 本案例呈现了在矩阵乘算子场景中，开启Matmul高阶API的纯Cube模式对算子性能的提升效果。如下图所示，Matmul API默认使用MIX模式，即用户从AIV侧发起消息，通过消息通信框架中转消息后，在AIC侧执行Matmul计算。这套消息处理机制会带来额外的Scalar性能开销。相较于MIX模式，纯Cube模式可以直接跳过消息通信框架，完成Matmul计算，提升算子性能。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_pure_cube.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Matmul高阶API开启纯Cube模式

## 案例介绍
本案例呈现了在矩阵乘算子场景中，开启Matmul高阶API的纯Cube模式对算子性能的提升效果。如下图所示，Matmul API默认使用MIX模式，即用户从AIV侧发起消息，通过消息通信框架中转消息后，在AIC侧执行Matmul计算。这套消息处理机制会带来额外的Scalar性能开销。相较于MIX模式，纯Cube模式可以直接跳过消息通信框架，完成Matmul计算，提升算子性能。
-   开启纯Cube模式的适用场景
非融合算子，只有矩阵计算的场景。即相较于MIX模式（包含矩阵计算和矢量计算），没有矢量计算的场景。本案例的算子规格如下：
算子用例规格
当前案例使用的AI处理器共24个核，每个核中包含1个AIC核和2个AIV核。
Tiling参数如下：
-   原始shape：M=128, N=30720, K=64。
-   单核shape：
-   MIX场景：按48个AIV核进行切分，singleCoreM=128，singleCoreN=640，singleCoreK=64。
-   纯Cube场景：按24个AIC核进行切分，singleCoreM=128，singleCoreN=1280，singleCoreK=64。
-   基本块shape：baseM=128，baseN=256，baseK=64。
-   L1相关Tiling参数：stepM=1，stepN=1，stepKa=4，stepKb=4，depthA1=8，depthB1=8。
## 获取性能数据
使用msOpProf工具获取算子仿真流水图和上板Profiling数据。因为纯Cube模式主要优化Scalar流水性能，可以重点分析Scalar的流水情况。
## 分析主要瓶颈点
-   优化前的Profiling数据如下，从C列的aic_time数据可以看出，多个核中最大算子执行耗时为17.85us。从G列的aic_scalar_time数据可以看出，Scalar平均耗时为15.02us，性能瓶颈在Scalar流水。
-   优化前的流水图如下，由于默认为MIX模式，每次Matmul计算均涉及消息通信框架对消息进行处理，Scalar流水重，性能开销较大，如下图红框所示。
## 设计优化方案
默认MIX模式下，用户在AIV侧发起消息，通过消息通信框架中转消息后，在AIC侧执行Matmul计算。基于这样的流程，用户使用Matmul高阶API编写算子代码时，可以使用REGIST_MATMUL_OBJ宏，无需区分AIV和AIC，但也因这套消息处理机制导致产生了额外的性能开销，如图1默认MIX模式的Matmul流程示意图所示。
实现默认MIX模式的具体步骤如下：
1.  Kernel侧，定义Matmul对象。
2.  Host侧，Matmul多核Tiling对象调用SetDim接口设置参与运算的核数。
3.  调用核函数，参考核函数定义和调用，设置核函数的numBlocks参数配置。
在没有矢量计算的算子场景下，可以跳过消息通信框架的机制，开启纯Cube模式完成Matmul计算，减少消息通信的性能开销，提升算子性能。
