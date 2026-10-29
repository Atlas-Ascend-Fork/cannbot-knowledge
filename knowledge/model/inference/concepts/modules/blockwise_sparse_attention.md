---
type: Concept
title: Blockwise Sparse Attention (TopK / SVG)
description: Blockwise Sparse Attention 是一种 Attention 组件变体：按 [block_Q, block_K] 粒度估计块的重要程度，只计算
  TopK 重要块、跳过其余块，从而把超长序列 DiT 的 Attention 计算量显著降低。与普通 sparse-flash-attention（按 Token
  TopK 的稀疏）并列，是 Attention 算法族下的"块级稀疏"分支。cann-recipes-infer 在 module/blockwise_sparse/
  下实现 TopK 与 SVG 两种 predictor，底层算子依赖 blitz_sparse_attention（需按参考文档自行编译）。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-22T01:42:26Z'
platforms:
- a2
- a3
---
# Blockwise Sparse Attention (TopK / SVG)

## Summary

**Blockwise Sparse Attention** 是一种 Attention 组件变体：按 `[block_Q, block_K]` 粒度估计块的重要程度，只计算 TopK 重要块、跳过其余块，从而把超长序列 DiT 的 Attention 计算量显著降低。与普通 [sparse-flash-attention](sparse_flash_attention.md)（按 Token TopK 的稀疏）并列，是 Attention 算法族下的"块级稀疏"分支。cann-recipes-infer 在 `module/blockwise_sparse/` 下实现 **TopK** 与 **SVG** 两种 predictor，底层算子依赖 [blitz_sparse_attention](https://gitcode.com/cann/ops-transformer/blob/ca41b0b5eb9dbf6eb94a58aa20fe379681c1d751/experimental/attention/blitz_sparse_attention/README.md)（需按参考文档自行编译）。

定位：这是 **Attention 算法/组件的变体**（不是正交的通用优化技术），放在 modules 目录下；与 [sparse-flash-attention](sparse_flash_attention.md)、[gated-attention](gated_attention.md)、[mla](mla.md) 并列。

## Mechanism

### TopK

分两个阶段：

1. **Offline profiling**：使用 Cumulative Attention Score Coverage (CAC) 作为保真度指标：

 $$
 CAC = \frac{\sum_{(i,j) \in \text{Top-K}} \text{Softmax}\left(\frac{QK^{T}}{\sqrt{d_{k}}}\right)_{ij}}{\sum_{i,j} \text{Softmax}\left(\frac{QK^{T}}{\sqrt{d_{k}}}\right)_{ij}}
 $$

 离线对每 step / layer / head 扫描不同稀疏度，找到满足目标 CAC 的最大稀疏度并落盘。代码位于 [`module/blockwise_sparse/offline_profiling/`](https://gitcode.com/cann/cann-recipes-infer/tree/2f82d10467e6fe8dae81c97a2cdac78d733a6703/module/blockwise_sparse/offline_profiling)。示例命令：

 ```bash
 python offline_profiling_hyvideo.py \
 --qk_dir_path /path/to/qk_dir \
 --target_dir_path /path/to/target_dir \
 --global_layer_num 60 --head_num 24 \
 --target_coverage 0.66 \
 --step_start 15 --step_end 50
 ```

2. **Online 推理**：将 q、k 按行分块并池化，估算注意力分数；对每行按离线稀疏度取 TopK 块，构造稀疏 mask 与 sabi tensor 喂入 blitz_sparse_attention。

### SVG (Sparse Video Generation)

```mermaid
flowchart LR
 Build[构造 spatial & temporal 两种稀疏 mask]
 Sample[每头采样一小部分 q] --> Calc[分别用两种 mask 做稀疏 attn<br/>与 full attn 比 MSE]
 Calc --> Pick[选 MSE 小的 pattern 作为该头类别]
 Build --> Pick
 Pick --> Run[根据构造好的 mask 跑稀疏 attention]
```

![SVG 稀疏模式](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-video/figures/svg.png)
*来源：[`docs/models/hunyuan-video/figures/svg.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/figures/svg.png)（cann-recipes-infer @ 2f82d10；原图来源 [ICML 2025 svg](https://icml.cc/virtual/2025/poster/43743)）*

## Variants

| Variant | 预测来源 | 稀疏粒度 | 适用阶段 |
|---------|---------|----------|----------| | TopK | 离线 profiling QK 统计分布 + 在线池化估算 | `[block_Q, block_K]` 块级 | 整个 step 区间可选 |
| SVG | 在线按头采样 MSE 选 spatial/temporal 模式 | 块级，两种固定模式 | `sparse_time_step` 区间内 |

## 与序列并行的协同

块稀疏只与单卡或 [ulysses](../parallelism/ulysses.md) 序列并行协同，**不与 [ring-attention](../parallelism/ring_attention.md) 组合**：HunyuanVideo `sample_video.py` 在 `sparse_method != "no_sparse"` 且 `ring_degree > 1` 时抛 `ValueError("Sparse attention does not support ring_degree > 1 in the current runtime.")`（"current runtime" 限制）。

- **Head 负载均衡（仅 TopK 路径）**：Ulysses 在 Attention 处切 head（`num_heads / ulysses_degree`）。块稀疏下各 head 的稀疏 mask 不同、实际计算量不均，故 `ulysses_degree > 1` 时调 `TopKPredictor.apply_head_reorder_for_load_balance(ulysses_degree)`（`sparse_method.py:593`）对 head 重排——按每 (step, layer) 的 head 计算量（`1 - sparsity`）降序贪心装箱到各 Ulysses rank，使各 rank 分到的稀疏计算量尽量均衡（具体重排算法详见 `sparse_method.py`）。该调用经 `sample_video.py` 的 `hasattr` 守卫触发——**仅 `TopKPredictor`（及 `HunyuanVideoTopKAdapter`）实现该方法；`SVGPredictor` 路径未实现、守卫下跳过不重排**。
- **SP 执行入口**：`parallel_sparse_attention`（`models/hunyuan-video/hyvideo/modules/attention.py:275`）在 Ulysses 下复用 SP 通信，按 `joint_q_local_bnsd` 等切分构造完整稀疏 attention 输入，内部走 `forward_ulysses_sparse`。
- **模型专用 predictor 适配器**：`HunyuanVideoTopKAdapter` / `HunyuanVideoSVGAdapter`（`sparse_method.py:1011 / 1263`，继承 `TopKPredictor` / `SVGPredictor`）承载 HunyuanVideo 双流/单流 DiT block 的稀疏接入（`hyvideo/sparse/sparse_block.py` 的 `sparse_double_block_forward` / `sparse_single_block_forward`），并携带 HyVideo 专属参数（`sink_frame_len`、`img_token_len`）。
- **与 Dit-Cache 互斥**：使能 sparse 会覆盖 block forward，与 [dit-cache](../techniques/dit_cache.md) 互斥（sparse YAML 固定 `dit_cache.method: NoCache`）。

来源的稀疏与负载均衡测量统一见[HunyuanVideo 稀疏观测草稿](../../optimizations/benchmark_observations/hunyuan_video_sparse_source_observations.md)；平台未绑定的测量不继承本机制的范围。

## 集成边界

块稀疏依赖模型专用的布局、predictor、算子以及并行切分；配置名称和允许的组合随版本变化。固定 2c45117 与后续 Ring 集成不能混用。启动、算子准备、配置及回退统一见[HunyuanVideo 版本化 Guide](../../guides/models/hunyuan_video_deployment.md)，缓存与稀疏的 forward 替换冲突仍须按对应版本核对。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md) 块稀疏 Attention 章节
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`module/blockwise_sparse/sparse_method.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/module/blockwise_sparse/sparse_method.py) 与 [`module/blockwise_sparse/offline_profiling/`](https://gitcode.com/cann/cann-recipes-infer/tree/2f82d10467e6fe8dae81c97a2cdac78d733a6703/module/blockwise_sparse/offline_profiling)
- 块稀疏 × SP 协同（@2c45117，MR!353 / MR!369）：[`sparse_method.py#L593`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/module/blockwise_sparse/sparse_method.py)（`apply_head_reorder_for_load_balance`）、`#L1011`/`#L1263`（`HunyuanVideoTopKAdapter` / `HunyuanVideoSVGAdapter`）、[`sample_video.py#L116-L126`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/sample_video.py)（ring_degree ValueError）、[`hyvideo/modules/attention.py#L275`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/hyvideo/modules/attention.py)（`parallel_sparse_attention`）、[`hyvideo/sparse/sparse_block.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/hyvideo/sparse/sparse_block.py)、[`docs/.../hunyuan_video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-video/hunyuan_video_optimization.md) `Ulysses + TopK/SVG 联合优化`

## Links

- [dit](dit.md)
- [sparse-flash-attention](sparse_flash_attention.md)
- [hunyuan-video](../models/hunyuan_video.md)
- [dit-cache](../techniques/dit_cache.md)
- [mm-inference-launch](../frameworks/mm_inference_launch.md)
- [ulysses](../parallelism/ulysses.md)
- [ring-attention](../parallelism/ring_attention.md)
