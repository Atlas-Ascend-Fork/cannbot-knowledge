---
type: Concept
title: Sana-Video
description: Sana-Video 的去噪网络、时序卷积与 VAE 职责，区分模型结构和平台 patch/量化方案。
tags:
- task.design
- topic.model_architecture
- topic.multimodal
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/sana-video/SANA-Video_optimization.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/sana-video/patches/npu_patches.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/sana-video/inference_video_scripts/inference_sana_video.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/README.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-21T10:02:02Z'
platforms:
- a2
- a3
- '950'
---



# Sana-Video

## Summary

Sana-Video 是SANA家族的视频生成模型；该实现以独立DiT去噪网络、VAE与文本编码器组成生成流程。去噪Block中的时序卷积与VAE不属于同一个优化对象。

平台配置、开关和验收步骤见[模型部署流程](../../guides/models/sana_video_deployment.md)，此处只保留模型机制。

## Architecture And Serving Traits

- 属于 DiT 范式的视频生成模型（见 [dit](../modules/dit.md)）；此处的卷积和融合算子 patch 面向去噪网络。推理脚本单独用 `get_vae` 创建 VAE，用 `build_model` 创建去噪模型，并对后者的 `model.blocks[*].mlp` 同步时序卷积权重
- 主要文件：
 - `models/sana-video/patches/npu_patches.py` — 全部 NPU 适配 patch
 - `models/sana-video/inference_video_scripts/inference_sana_video.py` — 推理脚本，负责权重转换与 patch 应用
- 无文档级 figures；无 SP / CFG / 并行优化描述

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/sana_video_deployment.md)：配置、开关、失效条件与回退入口。
- [Sana-Video 来源 A5（950）量化性能观测](../../optimizations/benchmark_observations/sana_video_950_source_benchmark.md)：固定来源自报，未经本仓独立复测。
- [Sana-Video BF16 来源表的平台细分缺口](../../optimizations/benchmark_observations/sana_video_bf16_source_observations.md)：来源条件待核验，保持draft。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/sana-video/SANA-Video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/sana-video/SANA-Video_optimization.md)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/sana-video/patches/npu_patches.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/sana-video/patches/npu_patches.py)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/sana-video/patches/quant_module.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/patches/quant_module.py)（`QuantLinear` / `QuantConv1x1AsLinear` / `QuantConv2d` / `replace_quant_module`、`LINEAR_MODES={a8w8,a4w4}`、`npu_dynamic_mx_quant` + `npu_quant_matmul`；MR!400 `ecbc110` Add SanaVideo 4bit/8bit quant）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/sana-video/patches/__init__.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/patches/__init__.py)（`VALID_QUANT_TYPES={bf16,a8w8,a4w4}`、`apply_all` `enable_quant`）、[`models/sana-video/inference_video_scripts/inference_sana_video.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/inference_video_scripts/inference_sana_video.py)（L555-556 `replace_quant_module`）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/sana-video/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/README.md)（`quant_type` bf16/a8w8/a4w4、Atlas 950 量化性能表、a4w4 部分回退 a8w8）、[`config/2b_480p_single_a8w8.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/config/2b_480p_single_a8w8.yaml) / [`config/2b_480p_single_a4w4.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/config/2b_480p_single_a4w4.yaml)

## Links

- [dit](../modules/dit.md)
- [vae](../modules/vae.md)
- [mm-inference-launch](../frameworks/mm_inference_launch.md)
- [hunyuan-video](hunyuan_video.md)
- [hunyuan-image-3](hunyuan_image_3.md)
- [wan2.2-i2v](wan2_2_i2v.md)
- [mxfp8-a8w8](../quantization/mxfp8_a8w8.md)（a8w8 = MXFP8 块级缩放数值格式）
- [hybrid-mxfp8-mxfp4](../quantization/hybrid_mxfp8_mxfp4.md)（a4w4 = MXFP4 `float4_e2m1fn_x2` 数值格式）

## Notes

固定来源未提供逐项消融或完整质量数据；A2/A3合并表与A5/950量化表保持独立，不推导SP/CFG等未覆盖的并行能力。
