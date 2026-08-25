---
type: Guide
title: 通过L0C Buffer数据暂存实现高效的矩阵乘结果累加
description: 【描述】算子实现中对矩阵乘的结果进行累加时（比如矩阵A1 \ B1 + A2 \ B2...结果的累加），可将前一次矩阵乘的结果暂存在L0C
  Buffer（CO1）上，调用Mmad接口实现矩阵乘结果累加。相比于每次矩阵乘的结果从L0C Buffer（CO1）搬运到GM上，再搬运到UB上进行累加计算，可减少数据搬运的次数，提升内存使用效率。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/matrix_compute/l0c_buffer_matmul_accumulate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 通过L0C Buffer数据暂存实现高效的矩阵乘结果累加

【优先级】高  __
【描述】算子实现中对矩阵乘的结果进行累加时（比如矩阵A1 * B1 + A2 * B2...结果的累加），可将前一次矩阵乘的结果暂存在L0C Buffer（CO1）上，调用Mmad接口实现矩阵乘结果累加。相比于每次矩阵乘的结果从L0C Buffer（CO1）搬运到GM上，再搬运到UB上进行累加计算，可减少数据搬运的次数，提升内存使用效率。
【反例】
优化前，算子进行2次矩阵乘结果累加的过程如下：
-   将前一次矩阵乘的计算结果从L0C Buffer（CO1）搬运到workspace上，再从workspace搬运到UB上；
-   下一次矩阵乘计算重复完成上述步骤将结果搬运到UB上；
-   在UB上将2次矩阵乘的结果相加。
当需要累加n次矩阵乘时，分别增加了n次L0C Buffer（CO1）->workspace、workspace->UB搬运以及n次Add运算。
【正例】
通过优化，算子对矩阵乘结果累加时，可将前一次矩阵乘的结果暂存在L0C上，通过Mmad接口参数cmatrixInitVal和cmatrixSource配置C矩阵的初始值，只调用2次Mmad接口实现2次矩阵乘结果累加。
