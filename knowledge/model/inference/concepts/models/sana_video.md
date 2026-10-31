---
type: Concept
title: Sana-Video
description: 当前Sana去噪/时序卷积/VAE分工、DP启动、离线文本权重及950混合量化边界。
tags:
- task.design
- topic.model_architecture
- topic.multimodal
- topic.precision
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/npu_patches.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/__init__.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/quant_module.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/inference_video_scripts/inference_sana_video.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:16:27Z'
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
 - `models/sana-video/patches/{__init__,npu_patches,quant_module}.py` — 导入/融合/量化补丁
 - `models/sana-video/inference_video_scripts/inference_sana_video.py` — 推理脚本，负责权重转换与 patch 应用
- 当前普通入口支持单机多卡DP（accelerate）；这不是单样本SP或CFG并行。量化档a8w8/a4w4仅950，a4w4仍保留部分a8w8。

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/sana_video_deployment.md)：配置、开关、失效条件与回退入口。
- [Sana-Video 950来源量化性能观测](../../optimizations/benchmark_observations/sana_video_950_source_benchmark.md)：固定来源自报，未经本仓独立复测。
- [Sana-Video BF16 来源表的平台细分缺口](../../optimizations/benchmark_observations/sana_video_bf16_source_observations.md)：来源条件待核验，保持draft。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/README.md)（primary）
- [npu_patches.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/npu_patches.py)（implementation）
- [__init__.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/__init__.py)（implementation）
- [quant_module.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/quant_module.py)（implementation）
- [inference_sana_video.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/inference_video_scripts/inference_sana_video.py)（implementation）

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

固定来源未提供逐项消融或完整质量数据；A2/A3合并表与950量化表保持独立，不推导SP/CFG等未覆盖的并行能力。
