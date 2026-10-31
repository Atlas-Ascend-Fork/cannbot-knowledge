---
type: Optimization
title: CFG 样本并行规则：比较双分支设备投入、通信与单步时延
description: CFG样本并行设备/通信取舍；更新Wan默认CFG2×Ulysses4并区分来源性能表CFG1×Ulysses8。
tags:
- task.debugging
- topic.diffusion
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/adaptor_patches/hunyuan_image_3_pipeline.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/config/14b_cfg2_ulysses4.yaml
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/README.md
  role: constraint
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:15:06Z'
platforms:
- a2
---

# CFG 样本并行规则：比较双分支设备投入、通信与单步时延

## 适用场景

模型在每个去噪/生成步做 classifier-free guidance（CFG）——需要一份 unconditional 预测和一份 conditional 预测，再按 `guided = uncond + scale·(cond − uncond)` 合成。无 CFG 并行时，可以把 cond/uncond 拼成 `batch ×2` 后一次前向，也可以按 pipeline 分别执行；二者不能混同，额外计算不等于时延必然翻倍。当集群卡数还能多分一维时，可把这两次独立前向摊到两组设备上并行。

适用：任意每步做 CFG 的生成模型（扩散 [dit](../../concepts/modules/dit.md)、文生图/图生视频 pipeline），且愿意用 2 倍设备换单步时延。

## 做什么

CFG 只是"同一网络吃两份无依赖的输入"，因此可分到两组设备并行，且这条轴与 [TP](../../concepts/parallelism/tensor_parallel.md) 正交：

- **样本级拆分**：CFG-parallel 组与 TP 组是两条独立通信轴，`world_size = cfg_parallel_size × tp_size(× sp_size)`。开 CFG 并行后每个 rank 只跑**一个**样本，per-rank 的 CFG batch 因子从 2 塌缩为 1（不再 `batch ×2`）。CFG 并行度固定为 2（cond/uncond 两样本）。
- **权重零重切**：每组设备跑的是同一张网络的同一份 TP 分片，只是喂不同的 cond/uncond 输入——打开 CFG 并行**不动权重切分**，只多一层进程分组，工程代价低。
- **一次 all_gather 互取**：两组各算出自己那半预测后，用一次 `all_gather`（`group=cfg_parallel_group`）让两组都拿到 `(pred_cond, pred_uncond)`，各自本地做 guidance 合成。这是唯一新增的跨组通信，量级为一份预测张量。关 CFG 并行时退化为把本地 `pred.chunk(2)` 拆两半。

CFG 组内的 all_gather / guidance 合成机制见 [cfg-parallel](../../concepts/parallelism/cfg_parallel.md)。

## 何时不适用 / 取舍

- CFG 并行吃掉 `cfg_size=2` 份设备，直接挤占同一集群里能给序列并行（[ulysses](../../concepts/parallelism/ulysses.md)）/ TP 的度，受 `world_size = cfg_size × sp_size × tp_size` 约束式限制。当前Wan默认YAML采用`cfg_size=2, ulysses_size=4`；README性能表却采用CFG1×Ulysses8，二者不是同一配置，缺同卡数CFG消融，不能据此判断哪种分配更划算。应按目标负载比较两种分配的通信、质量和时延。
- 仅在 CFG 组恰为 2 时走并行分支；关闭后回到来源 pipeline 的本地 cond/uncond 路径，具体是拼 batch 还是分别前向应核对实现。

## 参考实现及其约束

- HunyuanImage-3.0（文生图 DiT，Atlas A2/A3）：去噪循环里 `cfg_factor = 1 + do_classifier_free_guidance`，`cfg_parallel_size > 1` 时 `cfg_factor = 1`；guidance 段 `all_gather(cfg_preds_list, pred, group=cfg_parallel_group)` → `pred_cond, pred_uncond = cfg_preds_list`，与 VAE 并行并列为该样例新增的两个功能开关之一。示例排布 TP2+CFGP。
- [Wan2.2-I2V](../../concepts/models/wan2_2_i2v.md)（Atlas A2）：`--cfg_size N` 控 CFG 度，面向用户即 `nproc_per_node == cfg_size × ulysses_size`；`sample_guide_scale` 按 high/low-noise 边界在两档 guide_scale 间切；当前8卡默认`cfg_size=2, ulysses_size=4`；README性能表CFG1×Ulysses8不能直接作为该默认的结果。
- 上述开关名/配置是参考实现的细节，样本级正交并行的思想不受其约束。DiT 步间缓存与多卡并行的共存边界另见 [dit-cache-with-sequence-parallel](dit_cache_with_sequence_parallel.md)。

## Evidence

- [hunyuan_image_3_pipeline.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/adaptor_patches/hunyuan_image_3_pipeline.py)（primary）
- [14b_cfg2_ulysses4.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/config/14b_cfg2_ulysses4.yaml)（example）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/README.md)（constraint）
