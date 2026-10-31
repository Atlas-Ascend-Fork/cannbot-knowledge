---
type: Concept
title: HunyuanVideo
description: HunyuanVideo视频DiT、文本编码与VAE结构，统一YAML以及当前缓存、Ring稀疏和950 MXFP8入口。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.multimodal
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:13:04Z'
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
 - `models/hunyuan-video/config/*.yaml` — 统一运行、dit_cache、sparse配置
 - `models/hunyuan-video/scripts/` — 运行脚本
 - `module/unified_sp/{core.py, uaa.py}` — Ulysses / Ring / UAA
 - `module/dit_cache/cache_method.py` — DiT cache
 - `module/blockwise_sparse/{sparse_method.py, offline_profiling/}` — 块稀疏
 - `module/fa_quant/fa_quant.py` — MXFP8 量化 attention
 - `module/vae_patch_parallel.py` — VAE patch 并行

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/hunyuan_video_deployment.md)：配置、开关、失效条件与回退入口。
- [HunyuanVideo A3 累计优化的来源性能观测](../../optimizations/benchmark_observations/hunyuan_video_a3_source_benchmark.md)：固定来源自报，未经本仓独立复测。
- [HunyuanVideo 950PR 量化的来源性能表](../../optimizations/benchmark_observations/hunyuan_video_950_source_benchmark.md)：固定来源自报，未经本仓独立复测。
- [HunyuanVideo 稀疏与 Ring 的来源数据及平台缺口](../../optimizations/benchmark_observations/hunyuan_video_sparse_source_observations.md)：来源条件待核验，保持draft。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/README.md)（primary）
- [hunyuan_video_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md)（supporting）
- [sample_video.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py)（implementation）

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
