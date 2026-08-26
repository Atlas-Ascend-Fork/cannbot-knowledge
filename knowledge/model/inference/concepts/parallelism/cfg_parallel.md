---
type: Concept
title: CFG Parallel
description: Classifier-Free Guidance (CFG) 在 DiT 每个采样 step 内需要做两次前向：一次条件（cond，带 prompt）、一次无条件（uncond，空 prompt），再按 `noise_pred = noise_pred_uncond + w·(noise_pred_cond - noise_pred_uncond)` 融合。CFG Parallel 把这两个样本分别放到两张卡上同时跑，每卡只做一次模型推理，最后通过 all_gather 互相拿对方的结果，端到端相当于把 DiT 每步耗时减半。HunyuanImage-3.0、Wan2.2-I2V 均采用该并行。
tags:
- task.design
- topic.parallelism
- topic.mixture_of_experts
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# CFG Parallel

## Summary

Classifier-Free Guidance (CFG) 在 DiT 每个采样 step 内需要做两次前向：一次条件（cond，带 prompt）、一次无条件（uncond，空 prompt），再按 `noise_pred = noise_pred_uncond + w·(noise_pred_cond - noise_pred_uncond)` 融合。CFG Parallel 把这两个样本分别放到两张卡上同时跑，每卡只做一次模型推理，最后通过 all_gather 互相拿对方的结果，端到端相当于把 DiT 每步耗时减半。HunyuanImage-3.0、Wan2.2-I2V 均采用该并行。

## Mechanism

![CFG Parallel（TP2 + CFGP 为例）](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-image-3.0/figures/cfg_parallel.png)
*来源：[`docs/models/hunyuan-image-3.0/figures/cfg_parallel.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/figures/cfg_parallel.png)（cann-recipes-infer @ 2f82d10）*

> 源（HunyuanImage-3.0 优化文档）：对于一张图的生成，CFG(Classifier Free Guidance) 需要跑一个无条件的生成和一个有条件的生成，相当于网络跑了两个样本，可以把这两个样本拆分到两张卡上去跑，然后通过 all_gather 通信操作互相获取对方的计算结果，得到最终的预测结果。

Wan2.2-I2V 中的实现（`wan/image2video.py:L454`；源优化文档原文误作 `iamge2video.py`）：

```python
# 来源：docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md / wan/image2video.py
if get_classifier_free_guidance_world_size() == 2:
 noise_pred = model(
 latent_model_input, t=timestep, **arg_all, **extra_kwargs)[0].to(
 torch.device('cpu') if offload_model else self.device)
 noise_pred_cond, noise_pred_uncond = get_cfg_group().all_gather(
 noise_pred, separate_tensors=True
 )
else:
 noise_pred_cond = model(latent_model_input, t=timestep, **arg_c, **extra_kwargs)[0]
 noise_pred_uncond = model(latent_model_input, t=timestep, **arg_null, **extra_kwargs)[0]

noise_pred = noise_pred_uncond + sample_guide_scale * (noise_pred_cond - noise_pred_uncond)
```

```mermaid
flowchart LR
 subgraph Rank0[Rank 0 — cond]
 A0[DiT forward<br/>prompt embedding] --> B0[noise_pred_cond]
 end
 subgraph Rank1[Rank 1 — uncond]
 A1[DiT forward<br/>null embedding] --> B1[noise_pred_uncond]
 end
 B0 --> AG[all_gather<br/>CFG group]
 B1 --> AG
 AG --> Mix["noise_pred = uncond + w · (cond - uncond)"]
```

## Applicable Scenarios

- 所有使用 CFG 的扩散生成模型（HunyuanImage-3.0、HunyuanVideo、Wan2.2-I2V 等）
- 与 TP / SP 正交，可叠加形成 `TP × CFGP` 二维拓扑（HunyuanImage-3.0 文档以 TP2+CFGP 为例）
- DiT Cache（FBCache / TeaCache）下如需 `enable_separate_cfg = true`，cond/uncond 分开管理 cache（Wan2.2-I2V）

## Configuration

- CFG world_size = 2（固定为两路样本）
- 触发：`get_classifier_free_guidance_world_size() == 2`；否则退化为传统模式顺序跑两次
- TeaCache 与 CFG 串行配合：Wan2.2-I2V 采用 [ali-vilab/TeaCache 官方实现的 cond/uncond 分别管理版本](https://github.com/ali-vilab/TeaCache/tree/7c10efc4702c6b619f47805f7abe4a7a08085aa0/TeaCache4Wan2.1)

## Constraints

- 仅适用于需要 CFG 的推理，训练与蒸馏后无 CFG 的模型不适用
- 理论极限加速 ≈ 2×（每步减半），受通信（all_gather）与负载平衡影响
- 与 DiT Cache 合用时，若 cache 不分 cond/uncond，会导致两路跳步判断错位 → 必须启用 `enable_separate_cfg`

## Known Deployments

- **HunyuanImage-3.0**：CFG 并行 + TP + EP（MoE Double-Routing）
- **Wan2.2-I2V**：CFG 并行 + TeaCache（cond/uncond 分开管理）+ VAE 并行

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md) CFG 并行优化
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md) CFG 并行

## Links

- [ulysses](ulysses.md)
- [vae-patch-parallel](vae_patch_parallel.md)
- [dit-cache](../techniques/dit_cache.md)
- [dit](../modules/dit.md)
- [mm-inference-launch](../frameworks/mm_inference_launch.md)
- [hunyuan-image-3](../models/hunyuan_image_3.md)
- [wan2.2-i2v](../models/wan2_2_i2v.md)
- 跨域·具身：[cosmos-transfer2.5](../../../embodied/concepts/world_models/cosmos_transfer2_5.md)、[cosmos-predict2.5](../../../embodied/concepts/world_models/cosmos_predict2_5.md)（Cosmos 世界模型 CFG 并行）
