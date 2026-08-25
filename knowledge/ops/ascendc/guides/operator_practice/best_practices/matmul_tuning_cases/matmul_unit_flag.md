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

<!-- cannbot:related:start -->
## 相关

- [Iterate](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate.md)（`explains`）：Iterate 与《Matmul高阶API开启UnitFlag》的实质衔接是：Iterate 每次推进一块 baseM×baseN 并管理 L0C；Init/SetTensor 后需按同步模式配对 GetTensorC/Wait，IterateAll/NBatch/Batch 与异步指南给出替代执行契约。
- [Mmad计算关键特性说明](../../../../apis/simd_api/basic_api/cube_compute_tensor_api/mmad_compute_key_features/mmad_compute_key_features.md)（`explains`）：关键特性页只概述 UnitFlag；案例给出 enUnitFlag 开关、支持模板、与 L0C 累加/搬出组合的限制及适用瓶颈，能直接指导落地。
- [SetMMColumnMajor/SetMMRowMajor](../../../../apis/simd_api/basic_api/cube_compute/mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md)（`explains`）：SetMMColumnMajor/SetMMRowMajor 与《Matmul高阶API开启UnitFlag》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [SetMatmulConfigParams](../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_matmul_config_params.md)（`explains`）：《SetMatmulConfigParams》明确“在计算Tiling时，用于自定义设置表1中的MatmulConfig参数。本接口中配置的参数对应的功能在Tiling与Kernel中需要保持一致，所以本接口中的参数取值，需要与Kernel侧对应的MatmulConfig参数值保持一致，详细MatmulConfig参数请见表2。”；它与《Matmul高阶API开启UnitFlag》的“开启UnitFlag为MMAD与FIXPIPE提供512B细粒度同步，实现计算与搬出流水并行，提升算子性能。”在实际调用参数、数据流或结果校验上直接衔接。
- [UnitFlag](../../../../apis/simd_api/basic_api/cube_compute/mmad_compute_key_features/unit_flag.md)（`explains`）：《UnitFlag》给出“unitFlag的核心功能体现为：Mmad和FixPipe接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”；该约束/探针可直接复现、解释或前置验证《Matmul高阶API开启UnitFlag》中的“开启UnitFlag为MMAD与FIXPIPE提供512B细粒度同步，实现计算与搬出流水并行，提升算子性能。”。
- [UnitFlag](../../../../apis/simd_api/basic_api/cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`explains`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《Matmul高阶API开启UnitFlag》提供“开启UnitFlag为MMAD与FIXPIPE提供512B细粒度同步，实现计算与搬出流水并行，提升算子性能。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [中级性能优化](../../typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/intermediate_optimization.md)（`related`）：中级性能优化 与《Matmul高阶API开启UnitFlag》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [中级性能优化](../../typical_operator_cases/simd_operator_impl/matmul_matrix_operator/intermediate_optimization.md)（`related`）：中级性能优化 与《Matmul高阶API开启UnitFlag》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [高级极限打磨](../../typical_operator_cases/simd_operator_impl/matmul_matrix_operator/advanced_extreme_optimization.md)（`related`）：高级步骤 8 依赖 UnitFlag 重叠 MMAD 与 FIXPIPE，专项指南提供开关、依赖和验证细节。
- [高阶极限打磨](../../typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/extreme_optimization.md)（`related`）：高阶 Case 8 用 UnitFlag 让 MMAD 与 FIXPIPE 细粒度并行，专项指南展开其配置和验证方法。
<!-- cannbot:related:end -->
