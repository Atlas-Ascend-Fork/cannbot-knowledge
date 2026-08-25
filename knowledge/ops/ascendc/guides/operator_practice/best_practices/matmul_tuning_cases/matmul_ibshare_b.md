---
type: Guide
title: Matmul高阶API开启IBShare模板共享B矩阵数据
description: 本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，B矩阵开启IBShare对算子性能的提升效果。IBShare功能通过共享L1
  Buffer上相同的A矩阵或B矩阵数据，减少重复的MTE2数据搬运开销，提升算子性能。该功能支持A矩阵和B矩阵其中一个矩阵开启IBShare，也支持A矩阵和B矩阵同时开启IBShare。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_b.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Matmul高阶API开启IBShare模板共享B矩阵数据

## 案例介绍
本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，B矩阵开启IBShare对算子性能的提升效果。IBShare功能通过共享L1 Buffer上相同的A矩阵或B矩阵数据，减少重复的MTE2数据搬运开销，提升算子性能。该功能支持A矩阵和B矩阵其中一个矩阵开启IBShare，也支持A矩阵和B矩阵同时开启IBShare。
-   开启IBShare的适用场景
MIX场景（包含矩阵计算和矢量计算）下，多个AIV的A矩阵或B矩阵GM地址相同，且多个AIV复用的A矩阵或B矩阵在L1 Buffer上全载。
-   开启IBShare的约束条件
-   A矩阵和B矩阵同时开启IBShare的场景，同一算子中其它Matmul对象的A矩阵和B矩阵也必须同时开启IBShare。
-   A矩阵和B矩阵同时开启IBShare的场景，获取矩阵计算结果时，只支持调用IterateAll接口，且只支持输出到Global Memory。
本案例的算子规格如下：
算子规格
当前案例使用的AI处理器共20个核，每个核中包含1个AIC核和2个AIV核。因为输入shape较小，本案例以单核为示例，参考SetDim接口在MIX模式下的使用，在Tiling程序中设置参与运算的核数为2。Tiling参数如下：
-   原始shape：M=64, N= 256, K=384。
-   单核shape：singleCoreM=32，singleCoreN=256，singleCoreK=384。A矩阵拆成两半，一半在AIV0上处理，一半在AIV1上处理；AIV0和AIV1使用的B矩阵数据相同。
-   基本块shape：baseM=32，baseN=256，baseK=64。
-   L1缓存相关Tiling参数：stepM=1，stepN=1，stepKa=6，stepKb=6。
## 获取性能数据
使用msOpProf工具获取算子仿真流水图和上板Profiling数据，因为IBShare功能主要是通过共享L1 Buffer上相同的A矩阵或B矩阵数据，减少重复的MTE2数据搬运开销，所以重点分析MTE2的流水情况。
## 分析主要瓶颈点
-   优化前的流水图如下，不开启IBShare模板，默认使用的Norm模板。黑框标识AIV0发起的MTE2搬运流水：MTE2总共搬运了12次，其中A矩阵搬运了6次（stepM*stepKa=6），B矩阵搬运了6次（stepN*stepKb=6）。红框标识的AIV1发起的MTE2搬运流水，跟AIV0基本一致。在该案例中，因为AIV1使用的B矩阵跟AIV0使用的B矩阵数据相同，且singleCoreN=baseN*stepN，singleCoreK=baseK*stepKb，即B矩阵可以在L1全载。考虑在AIV0搬入B矩阵到L1 Buffer后，将B矩阵数据缓存在L1 Buffer上等待AIV1进行复用，进而节省B矩阵的MTE2重复搬运开销。
-   优化前的Profiling数据如下，C列的aic_time是10.29us，K列的aic_mte2_time是5.56us。

<!-- cannbot:related:start -->
## 相关

- [GetIBShareNormConfig](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_ib_share_norm_config.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《GetIBShareNormConfig》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [GetMatmulApiTiling](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_matmul_api_tiling.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《GetMatmulApiTiling》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [IterateAll](../../../../apis/simd_api/adv_api/convolution_compute/conv3_d_kernel/iterate_all.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《IterateAll》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [IterateAll](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate_all.md)（`explains`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《Matmul高阶API开启IBShare模板共享B矩阵数据》说明本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，B矩阵开启IBShare对算子性能的提升效果。IBShare功能通过共享L1 Buffer上相同的A矩阵或B矩阵数据，减少重复的MTE2数据搬运开销，提升算子性能。该功能支持A矩阵和B矩阵其中一个矩阵开启IBShare，也支持A矩阵和B矩阵同时开启IBShare。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [Matmul Kernel侧接口](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/matmul_kernel.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《Matmul Kernel侧接口》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [MatmulConfig](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/matmul_config.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《MatmulConfig》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [MatmulTemplateParams](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/matmul_template_params.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《MatmulTemplateParams》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [SetMatmulConfigParams](../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_matmul_config_params.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《SetMatmulConfigParams》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [GroupedMatmul算子性能调优案例](../grouped_matmul_tuning.md)（`related`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《GroupedMatmul算子性能调优案例》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [Matmul性能优化策略总览](matmul_optimization_overview.md)（`related`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《Matmul性能优化策略总览》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [Matmul算子优化Tiling策略](matmul_tiling_strategy.md)（`related`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《Matmul算子优化Tiling策略》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [Matmul高阶API开启MTE2 Preload](matmul_mte2_preload.md)（`related`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《Matmul高阶API开启MTE2 Preload》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../../simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md)（`related`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [Matmul高阶API开启IBShare模板共享A和B矩阵数据](matmul_ibshare_ab.md)（`same_topic`）：两篇 Matmul 案例都以 IBShare 复用 L1 数据：B-only 卡给出适用条件和 MTE2 收益，A+B 卡在同一决策上改为同时共享并验证 Scalar/Cube 收益，构成同一 IBShare 选型主题。
<!-- cannbot:related:end -->
