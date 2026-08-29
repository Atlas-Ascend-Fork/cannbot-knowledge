---
type: Guide
title: Matmul高阶API开启L2 Cache切分
description: 本案例呈现了在Matmul计算过程中，输入和输出的数据总量超过L2 Cache大小时，通过L2 Cache数据切分对算子性能的提升效果。开启L2
  Cache切分的完整样例请参考L2 Cache切分的算子样例。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_l2_cache_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Matmul高阶API开启L2 Cache切分

## 案例介绍
本案例呈现了在Matmul计算过程中，输入和输出的数据总量超过L2 Cache大小时，通过L2 Cache数据切分对算子性能的提升效果。开启L2 Cache切分的完整样例请参考L2 Cache切分的算子样例。
本案例使用的AI处理器的L2 Cache大小为192MB，L2 Cache纯读带宽约为GM的3到4倍，两者之间存在较大差距。在搬入或搬出相同数据量的情况下，访问L2 Cache内的数据比访问GM更快。若数据无法命中L2 Cache，即需要访问的数据不在L2 Cache内，导致需要访问GM进行读写，带宽利用效率较低，最终算子搬入或搬出数据成为算子整个运行过程的性能瓶颈。
-   开启L2 Cache切分的适用场景
输入和输出的数据量超过L2 Cache的大小。
本案例的算子规格如下：
算子规格
## 获取性能数据
使用msOpProf工具获取算子仿真流水图和上板Profiling数据。因为L2 Cache切分功能主要利用带宽更大的L2 Cache，减少MTE2数据搬运开销，所以重点分析MTE2的流水。
## 分析主要瓶颈点
当前案例基于Tiling全量常量化进一步优化，Tiling全量常量化请参考Matmul高阶API开启Tiling全量常量化案例。优化前的Profiling数据如下，C列的aic_time是867us，K列的aic_mte2_time是861.9us，MTE2占比为99%，MTE2数据搬运是当前算子性能的瓶颈。
## 设计优化方案
-   优化点一：调整切块大小和计算次数
-   优化前，输入数据不进行切分，所有核一次计算全部数据。如下图所示，图中数字表示核id，24个核一次计算A和B矩阵的所有数据。
-   优化后，输入数据被切分多次，所有核分多次计算，每个核单次计算只依赖切分后的数据量。L2 Cache切分方案确保单次计算的数据都在L2 Cache缓存中，搬运输入数据的效率更高。
-   优化点二：选择拖尾较小的L2 Cache切分方案
结合核间负载均衡的原理，AI处理器的物理核数固定，当数据进行L2 Cache切分之后，可能出现部分核有计算拖尾的情况，即每次所有核总计算量除以每个核单次处理的数据量不能被核数整除，导致每次计算的最后需要部分尾核计算剩余数据。而在尾核计算时，部分核始终处于空闲状态，导致算子的整体性能变差。下图中标黄的数据块就是尾块数据，左边方案由于拖尾，每次计算中0、1、2、3核多执行一次处理剩余数据。为达到全局负载最优，调整拖尾核的位置，如右边方案所示，完成所有计算时，0到7核均多一次数据块的计算。
在实际场景中，满足切分后的数据量小于L2 Cache大小的前提下，拖尾越小越好。基于这个原则可以确定L2 Cache切分块数。
-   优化点三：错位分核，减少左右矩阵同地址冲突问题
同地址冲突：多核并发执行Matmul计算时，如果多核同时访问输入矩阵的相同地址，会导致地址冲突，影响性能。
在M和N方向，将矩阵数据L2 Cache切分为大数据块，然后在数据块间错位分核，即将每个数据块依次沿对角线分配给不同的核处理，从而有效减少同地址冲突的问题。

<!-- cannbot:related:start -->
## 相关

- [L2CacheSplit](../../simd_operator_optimization/memory_access/l2_cache_split.md)（`same_topic`）：Matmul 案例的适用条件是“输入和输出的数据量超过L2 Cache的大小。”；通用指南给出决策“当输入和输出数据的数据量超过L2 Cache大小时，Tiling中开启L2 Cache切分策略。”。两卡围绕同一切分决策，案例进一步给出 Matmul 分块与拖尾选法。
<!-- cannbot:related:end -->
