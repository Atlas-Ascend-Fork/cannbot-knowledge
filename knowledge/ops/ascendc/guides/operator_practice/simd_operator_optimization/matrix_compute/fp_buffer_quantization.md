---
type: Guide
title: 通过FP Buffer存放量化参数实现高效随路量化
description: 【描述】算子实现中对矩阵乘结果进行量化计算时，可将量化参数搬运到Fixpipe Buffer（C2PIPE2GM）上，调用一次Fixpipe接口实现矩阵乘结果的量化计算。相比于将矩阵乘的结果从L0C
  Buffer（CO1）搬运到GM，再从GM搬运到UB，在UB进行量化计算的过程，数据搬运的次数更少，内存使用效率更高。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/matrix_compute/fp_buffer_quantization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2]
---

# 通过FP Buffer存放量化参数实现高效随路量化

【优先级】高
【描述】算子实现中对矩阵乘结果进行量化计算时，可将量化参数搬运到Fixpipe Buffer（C2PIPE2GM）上，调用一次Fixpipe接口实现矩阵乘结果的量化计算。相比于将矩阵乘的结果从L0C Buffer（CO1）搬运到GM，再从GM搬运到UB，在UB进行量化计算的过程，数据搬运的次数更少，内存使用效率更高。
【反例】
对矩阵乘结果进行量化计算的过程如下：
-   将矩阵乘的结果从L0C Buffer（CO1）搬运到workspace上；
-   再从workspace搬运到UB上；
-   将量化参数搬运到UB上，和矩阵乘的结果一起在UB上进行一系列量化计算；
-   将最终量化结果从UB搬运到GM上。
相比于正确示例多增加了L0C Buffer（CO1）->workspace、workspace->UB的搬运过程和量化的vector计算。
【正例】
该算子对矩阵乘的结果进行量化计算时，可将量化参数搬运到FB(Fixpipe Buffer)上，调用一次Fixpipe接口实现矩阵乘结果的量化计算。
