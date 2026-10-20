---
type: Guide
title: KDA 的门控分解与数值稳定性
description: 解释逐通道累计门控如何拆成矩阵乘法、为何选子块中点作参考，以及门控与求逆中间量的精度安排。
tags:
- task.design
- task.implementation
- topic.precision
- topic.tiling
status: stable
sources:
- resource: https://github.com/tile-ai/tilelang/blob/47976f210de3598444003e9b05de8204dfa7ff88/examples/kda/chunk_intra_token_parallel.py
  role: primary
- resource: https://github.com/flashserve/flash-linear-attention-npu/blob/f623f2b02ddd7a06b115d8061cc805275761a8b6/fla/ops/ascendc/kda/chunk_kda_fwd_prepare/op_kernel/arch22/chunk_kda_fwd_prepare_vec.h
  role: supporting
- resource: https://github.com/flashserve/flash-linear-attention-npu/blob/f623f2b02ddd7a06b115d8061cc805275761a8b6/fla/ops/ascendc/kda/chunk_kda_fwd_prepare/op_kernel/arch22/chunk_kda_fwd_prepare_cube.h
  role: supporting
created_at: '2026-10-17T09:07:03Z'
updated_at: '2026-10-17T09:19:48Z'
platforms:
- a2
aliases:
- KDA gate factorization
- Kplus Kminus
---

# KDA 的门控分解与数值稳定性

## 门控分解

KDA 的门控沿 K 通道变化。记 chunk 内累计的对数门控为 \(G_{i,d}=\sum_{t\le i}g_{t,d}\)，则带门控的点积为：

\[
A_{ij}=\sum_d k_{i,d}k_{j,d}e^{G_{i,d}-G_{j,d}}.
\]

门控在求和内部，不能先算普通 \(KK^T\) 再乘一个标量权重。可以构造 \(K^+=K\odot e^G\)、\(K^-=K\odot e^{-G}\)，将点积改写为 \(K^+(K^-)^T\)；QK 同理，将左侧 K 换成 Q。beta 和因果掩码另行应用。

在 TileLang 中，参考门控分解对应的计算分工是：在 `T.Scope("V")` 中生成缩放后的 Q/K tile，交给 `T.Scope("C")` 做矩阵乘法。

## 参考门控

衰减门控的 \(g\le0\)，累计后的 G 沿时间单调递减。直接计算 \(e^G\) 和 \(e^{-G}\)，会产生一侧很小、另一侧很大的中间值，即使最终的 \(e^{G_i-G_j}\) 没有溢出，分解后的因子也可能先溢出或下溢。引入逐通道参考值 R，改写为：

\[
K^+_i=k_i\odot e^{G_i-R},\qquad
K^-_j=k_j\odot e^{R-G_j}.
\]

同一个乘积的两侧使用相同的 R，指数中的参考值便会相消。将 chunk 再分成短子块，每个子块选其中间 token 的累计门控作为 R，可以平衡该子块两端的指数幅度。尾部子块按有效 token 范围取中点，不能取 padding 行。

时间中点是便于实现的选择，并非数学上唯一或总是最优的参考点：若门控衰减很不均匀，时间中点不等于门控数值范围的中点。它也不能保证所有指数都安全；跨子块计算时，右侧可能覆盖更长的历史前缀。

## 精度安排

累计门控、参考值相减、指数及缩放乘法保留 FP32，再将缩放后的 Q/K 转成低精度矩阵乘输入。

三角求解存在逐行依赖，误差还会经后续 W/U 和状态更新传播。小对角块求解与块间合并保留 FP32 中间量，合并完成后再转换为后续矩阵乘所需的 dtype。
