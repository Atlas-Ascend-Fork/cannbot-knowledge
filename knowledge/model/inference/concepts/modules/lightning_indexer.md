---
type: Concept
title: Lightning Indexer (LI)
description: LI 的加权 ReLU 打分与精确 TopK 模块，区分 V3.2 packed 缓存和 V4 压缩缓存及 HiF8/FP8/Int8 分支。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.speculative_decoding
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/indexer.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:22:24Z'
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

![LI 概念图](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/lightning-indexer.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/lightning-indexer.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/lightning-indexer.png)（cann-recipes-infer @ 944d2d3）*

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

相比 AscendC：开发效率更高（几百行 Python），支持动态 Shape；对应 shape 与相对调优披露见[算子调优来源观测](../../optimizations/benchmark_observations/operator_tuning_source_observations.md)，不在机制卡重复性能数字。

## 当前实现边界

V3.2 的 packed Query/Key 管理通过框架 CacheEntry 与 CP metadata；LI 输出 [T,1,K] 供稀疏注意力。V4 则仅 CSA 压缩缓存使用 LI，Key 长度为原始长度整除压缩比，另带余数；Int8、FP8、HiF8 分支与其 metadata 必须配对，HiF8不做Hadamard。当前接口与模式见[算子页](../kernels/lightning_indexer.md)，不能把 V3.2 的默认2048或Int8 scale套给所有模型。

## Performance Characteristics

- **TopK 精准计算**：基于昇腾排序指令（`VBS32` 分组 → `VMS4v2` 归并 → 耗尽模式规约）对 `Score` 全量排序，不使用近似算法。假设上下文长度 $S_k$，该固定排序实现的 TopK 总计算量估算 $\approx 4.36 S_k + 3.32 k$；其中规约部分无法精确评估，0.36 S_k + 3.32 k 来自来源以正态分布结合蒙特卡洛模拟的结果，不能作为任意 Score 分布的通用性能预测。
- **MTP 友好**：LI 的 K Cache 搬运与稠密 MLA 类似，MTP1 场景 Cube 计算量翻倍（2.15 → 4.29 GFlops）但 KV 搬运量不变（32 MB），计算访存比提升 → MTP 对 LI 有增益。对比来源分析中 SFA 在极端 MTP1 情况下 KV 搬运量可翻倍；是否发生取决于不同 query 的 TopK 复用，不能推广到所有 MTP 场景。
- **长序列耗时占比高**：LI 在长序列场景成为主要热点 —— 这是 V3.2-Exp 量化设计"主 Q_b_proj/W8A8、Indexer Q/K A8C8"的出发点之一。

## Evidence

- [deepseek_v3.2_exp_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md)（primary）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py)（implementation）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/indexer.py)（implementation）

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
