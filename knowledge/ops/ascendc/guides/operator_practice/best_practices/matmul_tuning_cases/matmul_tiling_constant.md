---
type: Guide
title: Matmul高阶API开启Tiling全量常量化
description: 将Matmul Tiling参数常量化到编译期，减少运行时Scalar计算开销，降低指令头开销并避免阻塞MTE2流水。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_constant.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Matmul高阶API开启Tiling全量常量化

## 案例介绍
本案例呈现了在使用Matmul高阶API进行矩阵乘法计算时，开启Matmul Tiling全量常量化对算子性能的提升效果。Matmul API在初始化和迭代过程中有大量Scalar计算，Matmul初始化时的Scalar计算影响指令头开销，Matmul迭代间的Scalar计算可能阻塞MTE2流水。在调用Matmul API实现矩阵乘法时，使用MatmulApiStaticTiling参数替代TCubeTiling变量参数，将Scalar计算提前到编译期进行，以减少运行时的Scalar计算开销，实现算子性能的提升。
-   Matmul Tiling常量化的适用场景：
-   Matmul初始化时的Scalar计算较多，影响指令头开销。
-   Matmul迭代之间的Scalar计算较多，阻塞MTE2流水。
-   Matmul Tiling常量化需要在编译期确定部分Tiling参数，根据确定参数的不同，分为全量常量化和部分常量化两种场景，使用Matmul Tiling常量化需要满足两种场景中任一场景的条件：
-   全量常量化：能够确定常量singleCore Shape（singleCoreM/singleCoreN/singleCoreK）和常量base Shape（basicM/basicN/basicK，也称baseM/baseN/baseK）。
-   部分常量化：能够确定常量base Shape（basicM/basicN/basicK，也称baseM/baseN/baseK）。
其中，全量常量化场景比部分常量化场景可以减少更多的Scalar计算开销。
本案例的算子规格如下：
算子规格
当前案例使用的AI处理器共24个核，每个核中包含1个AIC核和2个AIV核。
Tiling参数如下：
-   原始shape：M=128, N=30720, K=64。
-   单核shape：按24个AIC核进行切分，singleCoreM=128，singleCoreN=1280，singleCoreK=64。
对于B矩阵，沿着N轴进行切分，切分成24份的singleCoreN，单核上处理K * singleCoreN大小的数据。对于A矩阵，M轴不进行切分即singleCoreM=M，单核上处理singleCoreM * K大小的数据。总共24个核参与计算。
-   基本块shape：baseM=128，baseN=256，baseK=64。
-   L1相关Tiling参数：stepM=1，stepN=1，stepKa=4，stepKb=4，depthA1=8，depthB1=8。
## 获取性能数据
使用msOpProf工具获取算子仿真流水图和上板Profiling数据。相较于基础场景，Tiling常量化在编译期期间将部分或全部Tiling参数由变量转化为常数值，在算子执行时直接使用常量化的Tiling参数，可以减少Scalar性能开销，所以重点分析Scalar流水。

<!-- cannbot:related:start -->
## 相关

- [Matmul Tiling类使用说明](../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/matmul_tiling_usage.md)（`explains`）：使用MatmulApiStaticTiling参数替代TCubeTiling变量参数；调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数；连接常量化替代方案与常规动态 Tiling 基线。
<!-- cannbot:related:end -->
