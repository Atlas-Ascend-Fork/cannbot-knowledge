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

- [GetMatmulApiTiling](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_matmul_api_tiling.md)（`explains`）：GetMatmulApiTiling 与《Matmul算子优化Tiling策略》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [Matmul Tiling类](../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/matmul_tiling.md)（`explains`）：调优页说明如何据 shape/资源选择切分策略。
- [Matmul高阶API开启IBShare模板共享B矩阵数据](matmul_ibshare_b.md)（`related`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《Matmul算子优化Tiling策略》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [核间负载均衡](../../simd_operator_optimization/tiling_strategy/inter_core_load_balance.md)（`same_topic`）：核间负载均衡 与《Matmul算子优化Tiling策略》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
<!-- cannbot:related:end -->
