---
type: Guide
title: AIV核上的ND2NZ格式转换
description: 矩阵乘算子中输入矩阵内轴非256字节对齐时，在AIV核上完成ND到NZ格式转换以提升随路搬运效率。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/aiv_nd2nz_conversion.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AIV核上的ND2NZ格式转换

## 案例介绍
本案例展示了在矩阵乘算子场景中，使用Matmul高阶API进行计算，对内轴（内轴即矩阵的行方向）非256字节对齐的输入矩阵，在AIV核上进行ND2NZ格式转换对算子性能提升的效果。为提升Cube单元的计算效率，ND格式的输入矩阵在执行Cube计算前会先转换为NZ格式，ND格式和NZ格式的具体内容可参考数据格式。Matmul API内部使用随路ND2NZ指令同时进行格式转换以及数据搬运。但在数据非256字节对齐时，随路ND2NZ指令存在带宽利用率低的问题。因此输入矩阵的内轴非256字节对齐时，在进行Matmul计算前，利用AIV核上Vector计算单元完成ND格式到NZ格式的转换，可以避免随路非对齐数据搬运存在的效率低的问题，从而提升算子性能。
-   AIV核上的ND2NZ格式转换的适用场景
输入矩阵内轴非256字节对齐，且数据量较大影响随路格式转换的效率。
本案例的算子规格如下：
算子规格
当前案例使用的AI处理器共24个核，算子中开启高阶API Matmul的纯Cube模式。使用MDL模板，Tiling参数如下：
-   原始shape：M=1024, N= 4095, K=1024。
-   单核shape：singleCoreM=128，singleCoreN=1408，singleCoreK=1024。
-   基本块shape：baseM=128，baseN=256，baseK=64。
-   L1缓存相关Tiling参数：stepM=1，stepN=1，stepKa=4，stepKb=4。
## 获取性能数据
使用msOpProf工具获取算子仿真流水图和上板Profiling数据，重点分析MTE2的流水。
## 分析主要瓶颈点
-   优化前的Cube流水图如下，由于使用了随路ND2NZ指令，在MTE2数据搬运过程中进行数据格式的转换，导致MTE2整体占比较高。
-   优化前的Profiling数据如下，可以看到只使用Cube单元执行计算，aic_time最大耗时149.04us，其中aic_mte2_ratio占比很高。
## 设计优化方案
对于ND格式的输入矩阵，不再使用随路ND2NZ指令进行格式转换，而是利用Vector计算单元的能力完成数据格式转换。首先使用DataCopyPad接口，将非对齐的矩阵数据搬入Unified Buffer，使用Duplicate接口填充需要补为对齐位置的数据，再逐行调用Copy接口实现数据从ND到NZ格式的重排，将重排后的NZ数据写入workspace内存，最后直接读取workspace上的NZ数据，进行Matmul计算。
实现AIV核上的ND2NZ格式转换的主要步骤如下：
1.  创建Matmul对象时，定义内轴非256字节对齐的B矩阵的Format为NZ格式。
2.  利用Vector计算单元实现ND2NZ格式转换。如下代码中MatrixBtoNZ为将B矩阵的ND格式转换为NZ格式的函数，该函数的具体实现请参考完整样例代码。
3.  设置左矩阵A、右矩阵B、Bias，完成矩阵乘操作。
