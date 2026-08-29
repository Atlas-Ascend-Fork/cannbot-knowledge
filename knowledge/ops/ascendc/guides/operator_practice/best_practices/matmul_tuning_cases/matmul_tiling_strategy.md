---
type: Guide
title: Matmul算子优化Tiling策略
description: 本案例对Matmul算子进行性能分析和优化。Matmul算子实现的功能是矩阵乘法，其中主要包含数据搬入和搬出流水，Cube计算流水。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_strategy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2]
---

# Matmul算子优化Tiling策略

## 案例介绍
本案例对Matmul算子进行性能分析和优化。Matmul算子实现的功能是矩阵乘法，其中主要包含数据搬入和搬出流水，Cube计算流水。
以矩阵维度M = 4096，N = 5120，K = 4096，输入数据类型half，输出数据类型float，输出格式是ND为例，性能验证平台为Atlas A2 训练系列产品/Atlas A2 推理系列产品，介绍针对Matmul算子的优化手段，包括优化分核逻辑、优化基本块、开启大包搬运。
-   分核逻辑：开启尽量多的Cube核实现并行计算。
-   优化基本块，选择最优的baseM、baseN、baseK参数，其中baseM、baseN、baseK为Matmul Tiling中的参数。
-   开启大包搬运：从GM搬运数据到L1时，对于A矩阵，一次搬入depthA1个基本块，基本块大小为baseM * baseK，对于B矩阵，一次搬入depthB1个基本块，基本块大小为baseN * baseK。开启大包搬运后，一次搬入的数据量变大，从而提升MTE2搬运效率。
## 获取性能数据
使用msOpProf工具获取算子的Profiling数据，重点分析MTE2，Cube，Scalar pipeline的流水情况。
## 分析主要瓶颈点
由以上Profiling数据，可以看出MTE2耗时占比较大，当前性能瓶颈点在于MTE2流水。
-   Profiling数据的Block Dim可见分核未分满，考虑分核逻辑的优化。设CurrentCore是未优化前分核的Cube核数，MaxCore为最大Cube核数，当开启全部核并行做当前shape数据量的计算时，预估性能收益为MaxCore / CurrentCore的倍数。
-   优化基本块切分，将影响搬运数据的效率，算子搬运的总数据量为搬运的左矩阵和右矩阵数据量之和。在Matmul计算K方向不能全载的场景下，根据矩阵乘法的算法，搬运左矩阵的次数为N / baseN，搬运右矩阵的次数为M / baseM，即搬运总数据量totalCnt = (N / baseN) * M * K + (M / baseM) * K * N。预估性能收益为搬运数据量的比值，优化前搬运数据量totalCnt0/优化后搬运数据量totalCnt1，化简后结果为(1 / baseM0 + 1 / baseN0) / (1 / baseM1 + 1 / baseN1)，其中，baseM0, baseN0为优化前基本块参数，baseM1, baseN1为优化后基本块参数。
-   开启大包搬运后，指令条数变化、地址对齐等因素会影响性能，按照经验预估，对于MTE2为性能瓶颈的场景，会有20%以上的MTE2性能收益。
## 设计优化方案
-   优化点一：优化分核逻辑
由Profiling数据看出分核数为4，启动更多的核同时计算，可以提高计算并行度。当前案例使用的AI处理器共20个核，每个核中包含1个Cube Core和2个Vector Core。NPU调用程序中设置numBlocks为实际使用的核数20。

<!-- cannbot:related:start -->
## 相关

- [Matmul Tiling类使用说明](../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/matmul_tiling_usage.md)（`explains`）：优化基本块，选择最优的baseM、baseN、baseK参数，其中baseM、baseN、baseK为Matmul Tiling中的参数。；Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。。调优案例以 baseM/baseN/baseK 改善搬运效率，API 使用页给出获得 TCubeTiling 参数的入口，连接了性能选择与可执行配置步骤。
<!-- cannbot:related:end -->
