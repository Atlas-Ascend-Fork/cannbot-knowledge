---
type: Guide
title: 算子实现（SIMT算子实现）
description: 本章节将以Gather类算子为例，介绍SIMT算子实现的基本流程，如下图所示：
tags: [task.lookup, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simt_operator_impl/operator_impl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 算子实现

本章节将以Gather类算子为例，介绍SIMT算子实现的基本流程，如下图所示：
-   算子分析与核函数定义：明确算子的输入和输出，分析最大线程数的设置方案。明确算子核函数名、输入输出参数，确定动态参数空间大小，配置最大线程数。
-   Host侧线程切分计算：根据输入数据的shape信息，计算和设置gridDim、blockDim等参数。
-   Kernel侧算子实现：实现单线程内的计算逻辑。
下文将对上述步骤进行详细介绍。完整的算子实现请参考gather算子实现样例。
## 算子分析与核函数定义
算子分析具体步骤如下：
1.  明确算子的功能和计算逻辑。
gather算子的功能为从输入张量中获取指定索引行的数据，即从形状为M * N的二维张量input中获取指定索引的m行数据，这m行的行索引由输入index指定。算子输出output第i行数据的计算公式为：
2.  明确算子的输入和输出。
-   gather算子有两个输入：input与index；输出为output。
-   本样例中算子输入input的数据类型支持float、half、int32_t，index的数据类型为uint32_t，算子输出的数据类型与输入的数据类型相同。
-   每个线程处理一行数据，需要传入每行数据的长度in_width以及需要处理的总行数index_total_length，以确保尾部线程不会进行无效操作。
-   本样例中算子无需使用大量临时变量，因此直接将核函数的最大线程数设置为2048。
3.  明确函数名称和参数。
-   自定义核函数名称，本样例中核函数命名为gather_custom。
-   通过分析算子的输入和输出，使用模板参数来支持不同的输入输出数据类型。
函数入参定义如下：
4.  明确SIMT核函数gridDim、blockDim等动态参数设置方案。
-   本样例采用均匀切分方案，根据可用核数和最大线程数的限制，计算和调整gridDim（启用的线程块的个数）、blockDim（一个线程块启用的线程个数），同时保证gridDim不超过65535、blockDim不超过最大线程数2048。
-   本算子实现逻辑中无需使用动态UB空间。
通过以上分析，得到SIMT Gather算子的设计规格如下：
-   算子类型（OpType）：Gather
-   算子输入输出：
Gather算子输入输出规格
-   核函数名称：gather_custom
核函数定义如下：
## Host侧线程切分计算
本样例以简单的均匀切分方案介绍如何实现动态切分参数的计算。
1.  设置初始gridDim。
考虑到如果gridDim设置得比实际AIV核数少，会导致空闲核浪费，因此将初始gridDim设置为当前芯片的实际AIV核数量。AIV数量的获取方法如下所示：
2.  计算blockDim。
