---
type: Guide
title: 通过BT Buffer实现高效的bias计算
description: 【描述】算子中进行带bias的矩阵乘计算时，可将bias数据搬运至Bias Table Buffer（C2）上，调用一次Mmad接口实现矩阵乘加bias的计算，或者直接调用Matmul高阶API完成功能。相比于先将矩阵乘的结果从L0C
  Buffer（CO1）搬运到GM上，再搬运到UB上进行加bias的过程，减少了数据搬运的次数，可提升内存使用效率。数据流图对比如下：
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/matrix_compute/bt_buffer_bias_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 通过BT Buffer实现高效的bias计算

【优先级】高
【描述】算子中进行带bias的矩阵乘计算时，可将bias数据搬运至Bias Table Buffer（C2）上，调用一次Mmad接口实现矩阵乘加bias的计算，或者直接调用Matmul高阶API完成功能。相比于先将矩阵乘的结果从L0C Buffer（CO1）搬运到GM上，再搬运到UB上进行加bias的过程，减少了数据搬运的次数，可提升内存使用效率。数据流图对比如下：
【反例】
该算子进行带bias的矩阵乘计算时，过程如下：
-   将矩阵乘的计算结果从L0C Buffer（CO1）搬运到workspace上；
-   从workspace搬运到UB上；
-   在UB上进行加bias的运算；
-   最后将结果搬运到GM。
当循环n次该计算过程，则分别增加了n次L0C Buffer（CO1）->workspace、workspace->UB的搬运。
【正例】
该算子进行带bias的矩阵乘计算时，先将bias搬运到BT上，调用一次Mmad接口实现矩阵乘加bias的计算。
