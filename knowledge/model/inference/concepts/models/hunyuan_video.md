---
type: Concept
title: HunyuanVideo
description: HunyuanVideo 的视频 DiT、文本编码与 VAE 结构；并行、缓存、量化和性能按版本分开维护。
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
updated_at: '2026-10-22T10:36:46Z'
platforms:
- a2
- a3
- '950'
---



# HunyuanVideo

## Summary

HunyuanVideo 是文生视频DiT模型，文本编码、双流/单流去噪Block和VAE解码构成不同阶段。Attention与视频长序列相关，量化、稀疏或跨步缓存是部署选择，不能当作模型恒定结构或质量保证。

平台配置、开关和验收步骤见[模型部署流程](../../guides/models/hunyuan_video_deployment.md)，此处只保留模型机制。

## Architecture And Serving Traits

- **Backbone**：DiT（3D full attention），5s 720p ≈ 119k tokens 序列长度
- **双流/单流 Block**：Attention 按 `cu_seqlens` 分开有效图像+有效文本联合序列与剩余文本 padding，再拼接结果；首段长度是 img_len + text_mask.sum，不是图像/文本各自独立注意力
- **Text Encoder**：LLM + CLIP（源文档未展开）
- **目录结构**：
 - `models/hunyuan-video/sample_video.py` — 推理入口
 - `models/hunyuan-video/hyvideo/modules/{attention.py, norm_layers.py, posemb_layers.py, mxfp8_a8w8.py}` — 融合算子与量化
 - `models/hunyuan-video/hyvideo/sparse/sparse_config.yaml` — 块稀疏配置
 - `models/hunyuan-video/scripts/` — 运行脚本
 - `module/unified_sp/{core.py, uaa.py}` — Ulysses / Ring / UAA
 - `module/dit_cache/cache_method.py` — DiT cache
 - `module/blockwise_sparse/{sparse_method.py, offline_profiling/}` — 块稀疏
 - `module/fa_quant/fa_quant.py` — FP8 量化 attention
 - `module/vae_patch_parallel.py` — VAE patch 并行

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/hunyuan_video_deployment.md)：配置、开关、失效条件与回退入口。
- [HunyuanVideo A3 累计优化的来源性能观测](../../optimizations/benchmark_observations/hunyuan_video_a3_source_benchmark.md)：固定来源自报，未经本仓独立复测。
- [HunyuanVideo 950PR 量化的来源性能表](../../optimizations/benchmark_observations/hunyuan_video_950_source_benchmark.md)：固定来源自报，未经本仓独立复测。
- [HunyuanVideo 稀疏与 Ring 的来源数据及平台缺口](../../optimizations/benchmark_observations/hunyuan_video_sparse_source_observations.md)：来源条件待核验，保持draft。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md)（582 行完整优化实践）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/hunyuan-video/{README.md, sample_video.py, hyvideo/, scripts/}`](https://gitcode.com/cann/cann-recipes-infer/tree/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/hunyuan-video)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`module/{unified_sp/, dit_cache/, blockwise_sparse/, fa_quant/, vae_patch_parallel.py}`](https://gitcode.com/cann/cann-recipes-infer/tree/2f82d10467e6fe8dae81c97a2cdac78d733a6703/module)
- 块稀疏 × SP 协同（@2c45117，MR!353 / MR!369）：[`models/hunyuan-video/sample_video.py#L116-L126`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/sample_video.py)（ring_degree ValueError + apply_head_reorder_for_load_balance 调用）、[`hyvideo/modules/attention.py#L275`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/hyvideo/modules/attention.py)（`parallel_sparse_attention`）、[`docs/models/hunyuan-video/hunyuan_video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-video/hunyuan_video_optimization.md) `Ulysses + TopK/SVG 联合优化` 章节
- 块稀疏 Attention 性能表（TopK 76% / SVG 80%）：[cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md#不同块稀疏-attention算法的性能数据`](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/hunyuan-video/hunyuan_video_optimization.md)
- Ring + TopK / Ring + TopK + overlap 性能表与 Ring 路径块稀疏机制：[cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md#ring-attention--topksvg-性能数据`](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/hunyuan-video/hunyuan_video_optimization.md) `TopK/SVG + 序列并行联合优化` 章节

## Links

- [dit](../modules/dit.md)
- [vae](../modules/vae.md)
- [ulysses](../parallelism/ulysses.md)
- [ring-attention](../parallelism/ring_attention.md)
- [vae-patch-parallel](../parallelism/vae_patch_parallel.md)
- [dit-cache](../techniques/dit_cache.md)
- [blockwise-sparse-attention](../modules/blockwise_sparse_attention.md)
- [ring-attention-overlap](../techniques/ring_attention_overlap.md)
- [fp8-attention](../quantization/fp8_attention.md)
- [mxfp8-a8w8](../quantization/mxfp8_a8w8.md)
- [mm-inference-launch](../frameworks/mm_inference_launch.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [hunyuan-image-3](hunyuan_image_3.md)
- [wan2.2-i2v](wan2_2_i2v.md)
- [sana-video](sana_video.md)

## Notes

模块占比、累计加速与画质仅按独立观测的工作负载解释；不再假定所有表都是同一分辨率/帧数。HunyuanVideo此路径为dense DiT，不套用HunyuanImage的MoE路由。
