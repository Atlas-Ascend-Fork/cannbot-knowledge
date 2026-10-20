---
type: Guide
title: Chunk 下三角矩阵的分块求逆
description: 讲解单位下三角矩阵的小块逐行求解与大块递归合并，以及 Vector/Cube 的计算分工。
tags:
- task.design
- task.implementation
- topic.tiling
status: stable
sources:
- resource: https://github.com/tile-ai/tilelang-ascend/blob/585ad8c3b5fae175f1d1661059d347645f1f9536/examples/linear_attention_and_rnn/opt_gdn/opt_gdn_solve_tril.py
  role: primary
- resource: https://github.com/tile-ai/tilelang-ascend/blob/585ad8c3b5fae175f1d1661059d347645f1f9536/examples/linear_attention_and_rnn/opt_gdn_full.py
  role: example
created_at: '2026-10-17T05:38:17Z'
updated_at: '2026-10-17T09:19:48Z'
platforms:
- a2
aliases:
- solve_tril
- triangular inverse
- chunk inverse
---

# Chunk 下三角矩阵的分块求逆

Chunk GDN/KDA 需要计算 \(P=(I+A)^{-1}\)，其中 A 是严格下三角矩阵。利用三角结构，可以先求小对角块的逆，再用矩阵乘法合并成大块，而不必对完整矩阵反复做矩阵乘法。

## 32 阶：逐行求解

由 \((I+A)P=I\)，第 i 行满足：

\[
P_{i,:}=e_i^T-\sum_{j<i}A_{ij}P_{j,:},
\]

其中 \(e_i^T\) 是单位矩阵的第 i 行。计算当前行只需要前面已经求出的行，因此按行顺序推进；每行内部的加权求和由 Vector 完成。不同对角块可以独立求解。

在 TileLang 中，这部分放在 `T.Scope("V")`：行循环顺序执行，每行的加权求和用 `T.tile.broadcast`、`T.tile.mul` 和 `T.reduce_sum` 表达，对应 `opt_gdn_solve_tril.py` 的 32 阶求解。

## 64 阶：两个对角块与一个左下块

将 64×64 单位下三角矩阵按 32×32 分块：

\[
M=\begin{bmatrix}D_0&0\\L&D_1\end{bmatrix},
\qquad
M^{-1}=
\begin{bmatrix}
D_0^{-1}&0\\
-D_1^{-1}LD_0^{-1}&D_1^{-1}
\end{bmatrix}.
\]

两个 32 阶对角块的逆由 Vector 独立求解；得到它们后，左下块通过两次 32×32 矩阵乘法计算，由 Cube 完成。

TileLang 的 64 阶实现将对角求解放在 `T.Scope("V")`，块间组合放在 `T.Scope("C")`，通过两次 `T.gemm_v0` 依次计算 \(D_1^{-1}L\) 和 \((D_1^{-1}L)D_0^{-1}\)。128 阶复用相同的分工，扩大合并层级。

## 128 阶：逐层合并

沿用同一分块公式，分两层合并：

1. Vector 独立求出四个 32 阶对角块的逆。
2. 将相邻的两个对角块分别合成一个 64 阶逆，每组使用两次 32×32 矩阵乘法。
3. 将两个 64 阶逆作为对角块，再通过两次 64×64 矩阵乘法计算左下块，得到完整的 128 阶逆。

核心分工是：**Vector 求小对角块，Cube 合并块间结果。** 每个 chunk 的矩阵独立，可与其他 chunk 并行，见[任务切分](chunk_gdn_kda_task_partition.md)。
