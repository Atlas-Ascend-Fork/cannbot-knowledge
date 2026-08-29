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

- [GetIBShareNormConfig](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_ib_share_norm_config.md)（`explains`）：开启IBShare模板后，在L1 Buffer上是否同时缓存两块数据；IBShare功能通过共享L1 Buffer上相同的A矩阵或B矩阵数据，减少重复的MTE2数据搬运开销，提升算子性能。接口的 isDoubleCache 参数控制 L1 缓存块数，指南说明 B 共享的 MTE2 复用机制、适用 shape 与 IterateAll 输出约束。
- [IterateAll](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate_all.md)（`explains`）：案例硬约束“A矩阵和B矩阵同时开启IBShare的场景，获取矩阵计算结果时，只支持调用IterateAll接口，且只支持输出到Global Memory。”；IterateAll API定义“调用一次IterateAll，会计算出singleCoreM * singleCoreN大小的C矩阵。”。API卡给出案例唯一允许的结果获取调用及输出尺寸合同。
- [Matmul高阶API开启IBShare模板共享A和B矩阵数据](matmul_ibshare_ab.md)（`related`）：当A矩阵和B矩阵都启用IBShare时，可以一次性加载到L1 Buffer上，省去了切分，分开搬运的过程，同时Cube计算单元完全由AIV0单核驱动，发起一次计算，计算的结果由AIV0和AIV1共享，从而减少Cube响应的次数，减少Scalar计算。；IBShare功能通过共享L1 Buffer上相同的A矩阵或B矩阵数据，减少重复的MTE2数据搬运开销，提升算子性能。该功能支持A矩阵和B矩阵其中一个矩阵开启IBShare，也支持A矩阵和B矩阵同时开启IBShare。。B-only 案例给出 IBShare 的通用共享条件与同时开启约束，AB 案例进一步展示双矩阵全载后减少 Cube 响应和 Scalar 开销的路线。
<!-- cannbot:related:end -->
