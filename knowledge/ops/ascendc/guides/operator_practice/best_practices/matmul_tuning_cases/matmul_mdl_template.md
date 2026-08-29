---
type: Guide
title: Matmul高阶API开启MDL模板
description: 开启MDL模板使MTE2一次性搬入多个基本块到L1 Buffer，提升带宽利用率，减少搬运次数。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_mdl_template.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Matmul高阶API开启MDL模板

## 案例介绍
本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，开启MDL模板对算子性能的提升效果。在MDL模板中，MTE2流水从Global Memory到L1 Buffer（A1/B1）的数据搬运为一次性大包搬运，即一次MTE2能搬入多个Matmul计算的基本块，提升带宽利用率，使后续的MTE1流水尽可能复用A1/B1内基本块的缓存数据，减少MTE2的搬运次数。MDL模板的详细介绍请参考MatmulConfig。
-   MDL模板的适用场景
一般适用于MTE2循环搬运次数多的大shape场景，MDL模板在L1 Buffer（A1/B1）中缓存多次计算需要的数据，避免MTE2频繁搬运。
-   MDL模板的约束条件
MDL模板的TCubeTiling结构体需要满足TCubeTiling约束条件和MDL模板补充约束条件，具体请参考TCubeTiling结构体。
本案例的算子规格如下：
算子规格
当前案例使用的AI处理器共24个核，每个核中包含1个AIC核和2个AIV核。
Tiling参数如下：
-   原始shape：M=128, N=30720, K=1024。
-   单核shape：按24个AIC核进行切分，singleCoreM=128，singleCoreN=1280，singleCoreK=1024。
对于B矩阵，沿着N轴进行切分，切分成24份的singleCoreN，单核上处理K * SingleCoreN大小的数据。对于A矩阵，M轴不进行切分即singleCoreM=M，单核上处理singleCoreM * K大小的数据。总共24个核参与计算。
-   基本块shape：baseM=128，baseN=256，baseK=64。
-   L1相关Tiling参数：stepM=1，stepN=1，stepKa=4，stepKb=4，depthA1=8，depthB1=8。
## 获取性能数据
使用msOpProf工具获取算子仿真流水图和上板Profiling数据，因为MDL模板主要优化MTE2搬运效率，重点分析MTE2的流水情况。
## 分析主要瓶颈点
-   优化前的Profiling数据如下，Matmul默认为Norm模板。从C列的aic_time数据可以看出，多个核中最大算子执行耗时为83.68us。从C列的aic_time、L列的aic_mte2_time和M列的aic_mte2_ratio几组数据来看，MTE2平均耗时75.64us，耗时占比达到92%以上，因此需要优化MTE2流水的耗时。
-   优化前的流水图如下，MTE2分多次从Global Memory搬运基本块到L1 Buffer（A1/B1）。由于输入的矩阵Shape较大，MTE2循环搬运的次数多，但每次只搬运1个基本块，导致带宽利用率低，整体的MTE2搬运耗时长。进而影响后续的MTE1和MMAD流水，导致流水之间同步等待时间偏长。

<!-- cannbot:related:start -->
## 相关

- [MatmulConfig](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/matmul_config.md)（`explains`）：本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，开启MDL模板对算子性能的提升效果。在MDL模板中，MTE2流水从Global Memory到L1 Buffer（A1/B1）的数据搬运为一次性大包搬运，即一次MTE2能搬入多个Matmul计算的基本块，提升带宽利用率，使后续的MTE1流水尽可能复用A1/B1内基本块的缓存数据，减少MTE2的搬运次数。MDL模板的详细介绍请参考MatmulConfig。；模板参数MatmulConfig，用于配置Matmul模板信息以及相关的配置参数。不配置默认开启Norm模板，Norm模板的介绍请参考表模板特性。MatmulConfig的参数说明见表2。MatmulConfig的定义方式有： - 该模板参数可选取提供的模板之一，当前提供的MatmulConfig模板取值范围为【CFG_NORM、CFG_MDL、CFG_IBSHARE_NORM、MM_CFG_BB】，分别对应默认的Norm、MDL、IBShare、BasicBlock模板。各模板的介绍请参考表1。 - 该模板参数可以基于各类获取模板的接口，自定义模板参数配置，获取自定义模板。；案例要求开启 MDL，目标给出选择 CFG_MDL 的实际模板参数入口及默认 Norm 行为。
- [MatmulTemplateParams](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/matmul_template_params.md)（`explains`）：本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，开启MDL模板对算子性能的提升效果。在MDL模板中，MTE2流水从Global Memory到L1 Buffer（A1/B1）的数据搬运为一次性大包搬运，即一次MTE2能搬入多个Matmul计算的基本块，提升带宽利用率，使后续的MTE1流水尽可能复用A1/B1内基本块的缓存数据，减少MTE2的搬运次数。MDL模板的详细介绍请参考MatmulConfig。；创建Matmul对象时需要传入： - A、B、C、Bias的参数类型信息，类型信息通过MatmulType来定义，包括：内存逻辑位置、数据格式、数据类型、是否转置、数据排布和是否开启L1复用。 - MatmulConfig信息（可选），用于配置Matmul模板信息以及相关的配置参数。不配置默认使用Norm模板。；案例的 MDL 配置最终通过 Matmul 对象模板参数传入，目标补齐其与 A/B/C/Bias 类型信息的装配位置。
<!-- cannbot:related:end -->
