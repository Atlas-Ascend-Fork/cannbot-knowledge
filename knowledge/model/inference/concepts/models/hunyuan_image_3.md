---
type: Concept
title: HunyuanImage-3.0
description: 当前HunyuanImage的统一YAML、CFG每rank缓存修正、融合布局、A2回退与实际精度/稳态验收边界。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/config/ep8_cfg.yaml
  role: example
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:17:52Z'
platforms:
- a2
- a3
---

# HunyuanImage-3.0

## Summary

HunyuanImage-3.0 是MoE与DiT结合的文生图模型，去噪网络、文本输入和VAE解码承担不同职责。Attention、专家与CFG等并行维度来自不同模块，不能视为一组天然兼容的默认开关。

平台配置、开关和验收步骤见[模型部署流程](../../guides/models/hunyuan_image_3_deployment.md)，此处只保留模型机制。

## Architecture And Serving Traits

- **Backbone**：DiT 骨干 + MoE FFN，文本 encoder 为 Hunyuan 系 LLM
- **并行维度**：Attention 切头 + 线性行切 → Attention TP；MoE gate/up 列切 + down 行切；可切换 EP + DoubleRouting；CFG Parallel 在此基础上叠加
- **代码路径**：
 - `models/hunyuan-image-3.0/run_image_gen.py` — 生成入口
 - `models/hunyuan-image-3.0/model_adaptor.py` + `adaptor_patches/` — monkey patch 注入
 - `models/hunyuan-image-3.0/utils/` — 工具
 - `module/vae_patch_parallel.py` — VAE 并行（共享）

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/hunyuan_image_3_deployment.md)：配置、开关、失效条件与回退入口。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/README.md)（primary）
- [hunyuan_image_3_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md)（supporting）
- [hunyuan.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py)（implementation）
- [ep8_cfg.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/config/ep8_cfg.yaml)（example）

## Links

- [dit](../modules/dit.md)
- [vae](../modules/vae.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [cfg-parallel](../parallelism/cfg_parallel.md)
- [vae-patch-parallel](../parallelism/vae_patch_parallel.md)
- [double-routing](../techniques/double_routing.md)
- [moe-multi-stream](../techniques/moe_multi_stream.md)
- [mm-inference-launch](../frameworks/mm_inference_launch.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [hunyuan-video](hunyuan_video.md)

## Notes

- 当前YAML提供16卡EP8/Attention TP8并开启CFG/VAE的示例，不能当作任意负载最优值；来源缺完整受控性能表。
- 当前CFG并行按每rank batch分配StaticCache/position_ids，避免重复乘CFG因子；融合Attention切片显式contiguous。
- **gap**：文档提到 `HunyuanMoE` 类与 `HunyuanImage3ForCausalMM` 类，但未解释 `HunyuanImage-3.0` 的文本 tower 细节（是否为独立 LLM）
