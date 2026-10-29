---
type: Concept
title: HunyuanImage-3.0
description: HunyuanImage-3.0 的 DiT、MoE 与图像生成模块；并行、融合和部署差异分别引用任务入口。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-21T10:02:02Z'
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

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/hunyuan-image-3.0/{run_image_gen.py, model_adaptor.py, adaptor_patches/, utils/}`](https://gitcode.com/cann/cann-recipes-infer/tree/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/hunyuan-image-3.0)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`module/vae_patch_parallel.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/module/vae_patch_parallel.py)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — 统一推理拉起结构（@2c45117，@2f82d10 尚为 `demo.sh`）：[`models/hunyuan-image-3.0/infer.sh`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/infer.sh) + [`config/ep8_cfg.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/config/ep8_cfg.yaml)（`world_size: 16` / `moe-ep: true` / `entry_script: run_image_gen.py` / `CFG_PARALLEL=1` / `USE_VAE_PARALLEL=1`）+ [`config/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/config/README.md)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — MMReduceScatter A2 设备分支（@2c45117，commit 59a7906 MR!405）：[`adaptor_patches/hunyuan.py#L580-L607`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py)（`torch.npu.get_device_name()` / `"Ascend910B"` 设备分支：A2 走 `dist.reduce_scatter`、非 A2 走 `npu_mm_reduce_scatter_base`）+ [`docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md)（MMReduceScatter 句尾「(A2平台下暂未使能该融合算子)」）

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

- **gap**：源文档未给出 benchmark 数字、未列出 `attn_tp_size` / `moe_tp_size` / `ep_size` 推荐值
- **gap**：文档提到 `HunyuanMoE` 类与 `HunyuanImage3ForCausalMM` 类，但未解释 `HunyuanImage-3.0` 的文本 tower 细节（是否为独立 LLM）
