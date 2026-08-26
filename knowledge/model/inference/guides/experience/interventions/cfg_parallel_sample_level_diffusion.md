---
type: Guide
title: CFG 类生成模型用与 TP 正交的样本级并行摊平每步两次前向
description: CFG 类生成模型用与 TP 正交的样本级并行摊平每步两次前向。模型在每个去噪/生成步做 classifier-free guidance（CFG）——需要一份 unconditional 预测和一份 conditional 预测，再按 guided = uncond + scale·(cond − uncond) 合成。默认无 CFG 并行时，同一组设备把两个样本拼进 batch（batch ×2）串行跑两次网络，每步前向时延翻倍。当集群卡数还能多分一维时，可把这两次独立前向摊到两组设备上并行。 适用：任意每步做 CFG 的生成模型（扩散 dit、文生图/图生视频 pipeline），且愿意用 2 倍设备换单步时延。
tags:
- task.debugging
- topic.diffusion
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/218
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/49
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# CFG 类生成模型用与 TP 正交的样本级并行摊平每步两次前向

## 适用场景

模型在每个去噪/生成步做 classifier-free guidance（CFG）——需要一份 unconditional 预测和一份 conditional 预测，再按 `guided = uncond + scale·(cond − uncond)` 合成。默认无 CFG 并行时，同一组设备把两个样本拼进 batch（`batch ×2`）串行跑两次网络，每步前向时延翻倍。当集群卡数还能多分一维时，可把这两次独立前向摊到两组设备上并行。

适用：任意每步做 CFG 的生成模型（扩散 [dit](../../../concepts/modules/dit.md)、文生图/图生视频 pipeline），且愿意用 2 倍设备换单步时延。

## 做什么

CFG 只是"同一网络吃两份无依赖的输入"，因此可分到两组设备并行，且这条轴与 [TP](../../../concepts/parallelism/tensor_parallel.md) 正交：

- **样本级拆分**：CFG-parallel 组与 TP 组是两条独立通信轴，`world_size = cfg_parallel_size × tp_size(× sp_size)`。开 CFG 并行后每个 rank 只跑**一个**样本，per-rank 的 CFG batch 因子从 2 塌缩为 1（不再 `batch ×2`）。CFG 并行度固定为 2（cond/uncond 两样本）。
- **权重零重切**：每组设备跑的是同一张网络的同一份 TP 分片，只是喂不同的 cond/uncond 输入——打开 CFG 并行**不动权重切分**，只多一层进程分组，工程代价低。
- **一次 all_gather 互取**：两组各算出自己那半预测后，用一次 `all_gather`（`group=cfg_parallel_group`）让两组都拿到 `(pred_cond, pred_uncond)`，各自本地做 guidance 合成。这是唯一新增的跨组通信，量级为一份预测张量。关 CFG 并行时退化为把本地 `pred.chunk(2)` 拆两半。

CFG 组内的 all_gather / guidance 合成机制见 [cfg-parallel](../../../concepts/parallelism/cfg_parallel.md)。

## 何时不适用 / 取舍

- CFG 并行吃掉 `cfg_size=2` 份设备，直接挤占同一集群里能给序列并行（[ulysses](../../../concepts/parallelism/ulysses.md)）/ TP 的度，受 `world_size = cfg_size × sp_size × tp_size` 约束式限制。卡紧时把全部卡给 SP（`cfg_size=1`）通常比分 2 卡给 CFG 更划算——因此它是**可选能力、非默认路径**。
- 仅在 CFG 组恰为 2 时走并行分支；其余退化为单进程顺序两次前向即天然 rollback。

## 参考实现及其约束

- HunyuanImage-3.0（文生图 DiT，Atlas A2/A3）：去噪循环里 `cfg_factor = 1 + do_classifier_free_guidance`，`cfg_parallel_size > 1` 时 `cfg_factor = 1`；guidance 段 `all_gather(cfg_preds_list, pred, group=cfg_parallel_group)` → `pred_cond, pred_uncond = cfg_preds_list`，与 VAE 并行并列为该样例新增的两个功能开关之一。示例排布 TP2+CFGP。
- [Wan2.2-I2V](../../../concepts/models/wan2_2_i2v.md)（Atlas A2）：`--cfg_size N` 控 CFG 度，面向用户即 `nproc_per_node == cfg_size × ulysses_size`；`sample_guide_scale` 按 high/low-noise 边界在两档 guide_scale 间切；8 卡默认 `cfg_size=1, ulysses_size=8` 不开 CFG 并行。
- 上述开关名/配置是参考实现的细节，样本级正交并行的思想不受其约束。DiT 步间缓存与多卡并行的共存边界另见 [dit-cache-with-sequence-parallel](../../../optimizations/experience/rules/dit_cache_with_sequence_parallel.md)。

## Evidence

- `diff 事实`（HunyuanImage-3.0 @fdb79bf65a8b）：`hunyuan_image_3_pipeline.py` 去噪循环的 `cfg_factor` 塌缩 + `cfg_parallel_size>1` 分支 all_gather 互取；与优化文档「CFG并行优化」一致。溯源下探：[cann-recipes-infer-pr-218-feat-support-hunyuanimage-3-0-model-inference](https://gitcode.com/cann/cann-recipes-infer/merge_requests/218)
- `diff 事实`（Wan2.2-I2V, PR 合并 2025-10-30）：`image2video.py` 的 `get_classifier_free_guidance_world_size()==2` 分支 + `get_cfg_group().all_gather(..., separate_tensors=True)`，`parallel_mgr` 的 `use_cfg_parallel→cfg_degree=2`；「非默认、挤占 SP」取舍据 README（8 卡默认不开）。溯源下探：[cann-recipes-infer-pr-49-feat-add-wan2-2-i2v-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/49)
- 无独立性能数字，故不写加速幅度（理论减半单步前向时延）。
