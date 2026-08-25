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

<!-- cannbot:related:start -->
## 相关

- [Matmul开启AtomicAdd选项](matmul_atomic_add.md)（`related`）：“Matmul开启AtomicAdd选项”定义：【描述】__对于Matmul得到的结果矩阵C\(m, n\)，若后续需要和GM上的矩阵D\(m, n\)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩阵C的结果将直接累加到矩阵D的GM地址上，从而实现与矩阵D的Add操作。；“通过L0C Buffer数据暂存实现高效的矩阵乘结果累加”定义：【描述】算子实现中对矩阵乘的结果进行累加时（比如矩阵A1 \ B1 + A2 \ B2...结果的累加），可将前一次矩阵乘的结果暂存在L0C Buffer（CO1）上，调用Mmad接口实现矩阵乘结果累加。相比于每次矩阵乘的结果从L0C Buffer（CO1）搬运到GM上，再搬运到UB上进行累加计算，可减少数据搬运的次数，提升内存使用效率。。实质衔接：Matmul GM 搬出可用 SetAtomicAdd/enAtomic 直接累加 D；L0C 暂存是避免 GM 往返的另一方案，标量原子接口用于区分普通地址原子与搬出原子模式。
- [较小矩阵长驻L1 Buffer，仅分次搬运较大矩阵](small_matrix_l1_buffer.md)（`related`）：小矩阵长驻 L1 减少输入重复搬运，L0C 暂存则减少多轮输出累加写回；两者可组合优化 Matmul 数据流。
- [通过BT Buffer实现高效的bias计算](bt_buffer_bias_compute.md)（`related`）：焦点处理BT Buffer 承载 Matmul Bias 以减少搬运和等待；通过L0C Buffer数据暂存实现高效的矩阵乘结果累加正文说明“【描述】算子实现中对矩阵乘的结果进行累加时（比如矩阵A1 \ B1 + A2 \ B2...结果的累加），可将前一次矩阵乘的结果暂存在L0C Buffer（CO1）上，调用Mmad接口实现矩阵乘结果累加。相比于每次矩阵乘的结果从L0C Buffer（CO1）搬运到GM上，再搬运到”。候选是 Bias 计算的可替换暂存/累加路径或减少 AIC/AIV 等待的直接优化。
<!-- cannbot:related:end -->
