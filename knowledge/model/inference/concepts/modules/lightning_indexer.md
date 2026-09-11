---
type: Concept
title: Lightning Indexer (LI)
description: Lightning Indexer 是 DeepSeek-V3.2-Exp **DSA 架构**的前置稀疏选择模块 —— 对每个 query token，在长达数十万的上下文中**准确地**（非近似）选出 TopK（一般 2048）个相关 KV token 的 index，喂给后续 sparse-flash-attention。相比 MLA 它是一个轻量的类 MQA 结构，新增 `q_b_proj`、`wk_proj`、`weight_proj` 三个 Linear（综合所有层约 **+0.85B** 参数）。 LI 同时保留了一份**独立的 Indexer Key Cache**（与完整 MLA KVCache 并存），Decode 时免去重复计算；Indexer Key Cache 内存约 `batch × kv_length × Indexer_head_dim × bytes × num_layers`（4 batch × 64K × BF16 ≈ **4 GB**/rank）。 算子层实现见 lightning-indexer（AscendC / PyPTO / TileLang 三路）。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.speculative_decoding
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Lightning Indexer (LI)

## Summary

Lightning Indexer 是 DeepSeek-V3.2-Exp **DSA 架构**的前置稀疏选择模块 —— 对每个 query token，在长达数十万的上下文中**准确地**（非近似）选出 TopK（一般 2048）个相关 KV token 的 index，喂给后续 [sparse-flash-attention](sparse_flash_attention.md)。相比 MLA 它是一个轻量的类 MQA 结构，新增 `q_b_proj`、`wk_proj`、`weight_proj` 三个 Linear（综合所有层约 **+0.85B** 参数）。

LI 同时保留了一份**独立的 Indexer Key Cache**（与完整 MLA KVCache 并存），Decode 时免去重复计算；Indexer Key Cache 内存约 `batch × kv_length × Indexer_head_dim × bytes × num_layers`（4 batch × 64K × BF16 ≈ **4 GB**/rank）。

算子层实现见 [lightning-indexer](../kernels/lightning_indexer.md)（AscendC / PyPTO / TileLang 三路）。

## Mechanism

### 计算公式（非量化）

![LI 概念图](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/lightning-indexer.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/lightning-indexer.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/lightning-indexer.png)（cann-recipes-infer @ 2f82d10）*

对某个 token 对应的 Index Query $Q_{index} \in \mathbb{R}^{g \times d}$、上下文 Index Key $K_{index} \in \mathbb{R}^{S_k \times d}$、权重 $W \in \mathbb{R}^{g \times 1}$（g = GQA group size，d = per-head dim，$S_k$ = 上下文长度）：

$$
\text{Top-}k\left\{[1]_{1\times g}@\left[(W@[1]_{1\times S_{k}})\odot\text{ReLU}\left(Q_{index}@K_{index}^T\right)\right]\right\}
$$

拆成五步：

1. **BatchMatmul**：$S = Q_{index} \cdot K_{index}^T$
2. **激活**：$S' = \text{ReLU}(S)$
3. **广播乘**：$S_W = (W \cdot \mathbf{1}_{1\times S_k}) \odot S'$
4. **沿 G 轴 ReduceSum**：$Score = \mathbf{1}_{1\times g} \cdot S_W$
5. **Top-k**：对 $Score$ 取数值排序前 k 个的 index

Prefill 或 MTP Decode 场景下多个 token 的 $Q_{index}$ 会合并统一计算。

### 量化公式（LightningIndexerQuant）

$Q_{index}$ 与 $K_{index}$ 均 INT8，引入反量化系数 $Scale_Q, Scale_K$：

$$
\text{Top-}k\left\{[1]_{1\times g}@\left[(W@[1]_{1\times S_{k}})\odot\text{ReLU}\left(\left(Scale_Q@Scale_K^T\right)\odot\left(Q_{index}^{INT8}@{(K_{index}^{INT8})}^T\right)\right)\right]\right\}
$$

AscendC 实现用 **Mat-Duce 算法**把这步 ReduceSum 转成矩阵乘，大部分计算在 Cube 核内完成，充分利用 FixP 随路 DEQF16 / ReLU。详见 [lightning-indexer](../kernels/lightning_indexer.md) "LI 量化支持"段。

## Variants

### 非量化版 `npu_lightning_indexer`

纯 BF16 / FP16 输入。模型代码（`models/indexer.py:L450`）：

```python
return torch_npu.npu_lightning_indexer(**li_input_kwargs)[0]
```

### 量化版 `npu_quant_lightning_indexer` (A8C8)

量化路径走的是一个**独立命名的 fused op** `npu_quant_lightning_indexer`，而非给非量化版 `npu_lightning_indexer` 额外传 A8C8 参数。入口由 `kv_cache_quant_mode == "int8"` 分支决定（`models/indexer.py:L448`）：

```python
return torch_npu.npu_quant_lightning_indexer(**li_input_kwargs)
```

Indexer Q 走动态 **Per-Token-Head A8**；Indexer Cache 走**Per-Token-Head C8**；反量化系数以 FP16 存储（`weights` 也转 `torch.float16`）。量化前对 Q/K 做 **Hadamard 变换**（通过矩阵右乘 `hadamard_q` / `hadamard_k`）消除 outlier。见 [indexer-prolog](../kernels/indexer_prolog.md)。

### PyPTO 版 `npu_lightning_indexer_pto`

PyPTO 自研框架实现（`ops/pypto/src/lightning_indexer_pto/`）。`models/indexer.py:L452`：

```python
topk_indices = torch.ops.custom_pypto.npu_lightning_indexer_pto(**li_input_kwargs)
```

相比 AscendC：开发效率更高（几百行 Python），支持动态 Shape；在典型 Shape（4 batch × 64K）下经过 Tile/L1 复用调优后性能提升 ~27%（见 [lightning-indexer](../kernels/lightning_indexer.md) PyPTO 调优段）。

## Performance Characteristics

- **TopK 精准计算**：基于昇腾排序指令（`VBS32` 分组 → `VMS4v2` 归并 → 耗尽模式规约）对 `Score` 全量排序，不使用近似算法。假设上下文长度 $S_k$，TopK 总计算量 $\approx 4.36 S_k + 3.32 k$。
- **MTP 友好**：LI 的 K Cache 搬运与稠密 MLA 类似，MTP1 场景 Cube 计算量翻倍（2.15 → 4.29 GFlops）但 KV 搬运量不变（32 MB），计算访存比提升 → MTP 对 LI 有增益。对比 SFA 的 MTP 翻倍 KV 搬运量、难以加速。
- **长序列耗时占比高**：LI 在长序列场景成为主要热点 —— 这是 V3.2-Exp 量化设计"主 Q_b_proj/W8A8、Indexer Q/K A8C8"的出发点之一。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md)（LI 架构地位、KVCache 分析、MTP 收益对比表）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_ascendc_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_ascendc_operator_guide.md)（LI 计算公式、Mat-Duce、TopK 指令实现）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md)（PyPTO 版本 LI / Indexer Prolog 计算公式）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md)（TileLang LI Cube/Vector 分解）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v3.2-exp/models/indexer.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek-v3.2-exp/models/indexer.py)（`Indexer`、`prefill_decode_ascendc` / `prefill_decode_pypto` 两条路径入口）

## Links

- [deepseek-v3.2-exp](../models/deepseek_v3_2_exp.md)
- [deepseek-v4](../models/deepseek_v4.md)（V4 CSA 层强化 LI + Compress Ratio）
- [sparse-flash-attention](sparse_flash_attention.md)
- [mla](mla.md)
- [lightning-indexer](../kernels/lightning_indexer.md)
- [indexer-prolog](../kernels/indexer_prolog.md)
- [deepseek-indexer-attention](../kernels/deepseek_indexer_attention.md)
- [ascendc](../frameworks/ascendc.md)
- [pypto](../frameworks/pypto.md)
- [tilelang](../frameworks/tilelang.md)
- [w8a8c8](../quantization/w8a8c8.md)
- [dsa](dsa.md)（顶层架构模式：LI 是 DSA 的 indexer overlay 实例）