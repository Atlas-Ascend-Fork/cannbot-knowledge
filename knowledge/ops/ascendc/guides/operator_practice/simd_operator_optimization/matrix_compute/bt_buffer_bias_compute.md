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

<!-- cannbot:related:start -->
## 相关

- [Matmul开启AtomicAdd选项](matmul_atomic_add.md)（`related`）：焦点处理BT Buffer 承载 Matmul Bias 以减少搬运和等待；Matmul开启AtomicAdd选项正文说明“【描述】__对于Matmul得到的结果矩阵C\(m, n\)，若后续需要和GM上的矩阵D\(m, n\)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩”。候选是 Bias 计算的可替换暂存/累加路径或减少 AIC/AIV 等待的直接优化。
- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../pipeline_scheduling/enable_iterate_avoid_sync.md)（`related`）：焦点处理BT Buffer 承载 Matmul Bias 以减少搬运和等待；启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖正文说明“MIX场景下推荐使用Iterate或IterateAll异步接口，减少Cube与Vector核间消息交互，降低通信开销”。候选是 Bias 计算的可替换暂存/累加路径或减少 AIC/AIV 等待的直接优化。
- [通过FP Buffer存放量化参数实现高效随路量化](fp_buffer_quantization.md)（`related`）：焦点处理BT Buffer 承载 Matmul Bias 以减少搬运和等待；通过FP Buffer存放量化参数实现高效随路量化正文说明“【描述】算子实现中对矩阵乘结果进行量化计算时，可将量化参数搬运到Fixpipe Buffer（C2PIPE2GM）上，调用一次Fixpipe接口实现矩阵乘结果的量化计算。相比于将矩阵乘的结果从L0C Buffer（CO1）搬运到GM，再从GM搬运到UB，在UB进行量化计算的过程，”。候选是 Bias 计算的可替换暂存/累加路径或减少 AIC/AIV 等待的直接优化。
- [通过L0C Buffer数据暂存实现高效的矩阵乘结果累加](l0c_buffer_matmul_accumulate.md)（`related`）：焦点处理BT Buffer 承载 Matmul Bias 以减少搬运和等待；通过L0C Buffer数据暂存实现高效的矩阵乘结果累加正文说明“【描述】算子实现中对矩阵乘的结果进行累加时（比如矩阵A1 \ B1 + A2 \ B2...结果的累加），可将前一次矩阵乘的结果暂存在L0C Buffer（CO1）上，调用Mmad接口实现矩阵乘结果累加。相比于每次矩阵乘的结果从L0C Buffer（CO1）搬运到GM上，再搬运到”。候选是 Bias 计算的可替换暂存/累加路径或减少 AIC/AIV 等待的直接优化。
<!-- cannbot:related:end -->
