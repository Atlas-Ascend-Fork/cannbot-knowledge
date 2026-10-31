---
type: Concept
title: Wan2.2-I2V
description: Wan2.2-I2V图文条件、双噪声DiT与VAE，当前CFG默认配置和单卡缓存接入边界。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.multimodal
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/generate.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:15:06Z'
platforms:
- agnostic
---

# Wan2.2-I2V

## Summary

Wan2.2-I2V 为图生视频模型，输入参考图像与文本prompt，经DiT去噪与VAE解码生成视频。CFG涉及有条件/无条件预测，缓存这些状态时不能混用分支。

平台配置、开关和验收步骤见[模型部署流程](../../guides/models/wan2_2_i2v_deployment.md)，此处只保留模型机制。

## Architecture And Serving Traits

模型实现入口为generate.py，去噪与Attention位于wan/modules，图像条件生成由image2video.py组织。通用DiT/VAE、CFG和cache的机制见相关专题；具体版本的启动、融合与并行由模型Guide维护。

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/wan2_2_i2v_deployment.md)：配置、开关、失效条件与回退入口。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/README.md)（primary）
- [generate.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/generate.py)（implementation）
- [wan2.2-i2v_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md)（supporting）

## Links

- [dit](../modules/dit.md)
- [vae](../modules/vae.md)
- [ring-attention](../parallelism/ring_attention.md)
- [cfg-parallel](../parallelism/cfg_parallel.md)
- [vae-patch-parallel](../parallelism/vae_patch_parallel.md)
- [dit-cache](../techniques/dit_cache.md)
- [ring-attention-overlap](../techniques/ring_attention_overlap.md)
- [mm-inference-launch](../frameworks/mm_inference_launch.md)
- [hunyuan-video](hunyuan_video.md)
- [hunyuan-image-3](hunyuan_image_3.md)

## 当前接入边界

当前默认多卡CFG2×Ulysses4并启用VAE并行；README的性能表另采用CFG1×Ulysses8，不能混作同一结果。FB/Tea只用于单卡接入，多卡入口强制NoCache；当前文档已修正LayerNorm调制scale入参，不保留旧缺陷断言。
