---
type: Guide
title: Matmul高阶API开启IBShare模板共享A和B矩阵数据
description: 本案例呈现了在融合算子场景中，使用Matmul高阶API进行矩阵乘法计算时，A矩阵和B矩阵同时启用IBShare对性能的提升效果。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_ab.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Matmul高阶API开启IBShare模板共享A和B矩阵数据

## 案例介绍
本案例呈现了在融合算子场景中，使用Matmul高阶API进行矩阵乘法计算时，A矩阵和B矩阵同时启用IBShare对性能的提升效果。
该案例的关键优化措施包括：
-   分核逻辑：以Cube核视角分核，Matmul计算结果输出到GM，提供给Vector核进行后续计算。
-   开启IBShare：A矩阵和B矩阵同时开启IBShare。
本案例的算子规格如下：
算子规格
开启IBShare和未开启IBShare的完整样例请参考A、B矩阵均开启IBShare样例。
## 获取性能数据
使用msOpProf工具获取算子的Profiling的数据，重点分析MTE2，Cube，Scalar的流水情况。
## 分析主要瓶颈点
通过分析以上Profiling数据可以看出，算子执行多次的平均耗时为27.11us，aic_scalar_time的平均耗时为26.27us，当前性能瓶颈点为Cube的Scalar流水。
## 设计优化方案
A矩阵和B矩阵均未开启IBShare时，数据需要根据K轴、M轴或N轴进行切分计算。这里以K轴切分为例，未开启IBShare之前，算子以AIV Block为视角进行tiling切分，AIV0发起A0*B0的计算，AIV1发起A1*B1的计算。
当A矩阵和B矩阵都启用IBShare时，可以一次性加载到L1 Buffer上，省去了切分，分开搬运的过程，同时Cube计算单元完全由AIV0单核驱动，发起一次计算，计算的结果由AIV0和AIV1共享，从而减少Cube响应的次数，减少Scalar计算。
开启IBShare和不开启IBShare的数据交互对比示意图如下：
通过设置A和B矩阵MatmulType的IBShare均为true，开启该优化，具体代码如下：
## 验证优化方案性能收益
优化后执行多次的平均耗时：22.44us，较优化前有较大提升。
## 总结
融合算子场景下，Matmul A矩阵和B矩阵同时开启IBShare，以Cube核视角分核，可以有效减少Cube侧的Scalar开销，提升性能。

<!-- cannbot:related:start -->
## 相关

- [GetIBShareNormConfig](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_ib_share_norm_config.md)（`explains`）：用于配置IBShare模板的参数，获取自定义IBShare模板；通过设置A和B矩阵MatmulType的IBShare均为true，开启该优化。接口提供 IBShare 模板配置入口，指南展示 A/B 同时共享时的 MatmulType 设置、Cube 分核与 27.11us 到 22.44us 的验证路径。
- [Matmul高阶API开启IBShare模板共享B矩阵数据](matmul_ibshare_b.md)（`related`）：当A矩阵和B矩阵都启用IBShare时，可以一次性加载到L1 Buffer上，省去了切分，分开搬运的过程，同时Cube计算单元完全由AIV0单核驱动，发起一次计算，计算的结果由AIV0和AIV1共享，从而减少Cube响应的次数，减少Scalar计算。；IBShare功能通过共享L1 Buffer上相同的A矩阵或B矩阵数据，减少重复的MTE2数据搬运开销，提升算子性能。该功能支持A矩阵和B矩阵其中一个矩阵开启IBShare，也支持A矩阵和B矩阵同时开启IBShare。。B-only 案例给出 IBShare 的通用共享条件与同时开启约束，AB 案例进一步展示双矩阵全载后减少 Cube 响应和 Scalar 开销的路线。
<!-- cannbot:related:end -->
