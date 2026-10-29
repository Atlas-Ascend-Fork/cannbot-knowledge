---
type: Concept
title: Wan2.2-I2V
description: Wan2.2-I2V 的图文输入、DiT 去噪和 VAE 解码职责，部署并行与缓存另行维护。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-21T10:02:02Z'
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

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/wan2.2-i2v/{generate.py, run.sh, set_env.sh, wan/}`](https://gitcode.com/cann/cann-recipes-infer/tree/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/wan2.2-i2v)
- 旧文档的 `module/dit_cache_step/cache_step.py` 在上述固定提交下获取失败；不把该链接当作已恢复的实现，版本入口见模型Guide。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — 统一推理拉起（`infer.sh` + `config/`，引入于 refactor commit 06656b0）：[`models/wan2.2-i2v/infer.sh`](https://gitcode.com/cann/cann-recipes-infer/blob/06656b0519fde3256eed1b2a77e5327898e0b00f/models/wan2.2-i2v/infer.sh)、[`config/14b_cfg2_ulysses4.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/06656b0519fde3256eed1b2a77e5327898e0b00f/models/wan2.2-i2v/config/14b_cfg2_ulysses4.yaml)

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

## Notes

旧优化文档未给端到端benchmark；其FusedLayerNormModulate片段存在scale未定义，不能直接作为配置/修复配方。文档拼写iamge2video.py不等于实际源码入口。
