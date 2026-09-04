---
type: Runbook
title: 视频 DiT（I2V）单卡推理 OOM：降到标称之下的分辨率，或大规格转多卡序列并行
description: 视频 DiT（I2V）单卡推理 OOM：降到标称之下的分辨率，或大规格转多卡序列并行。大参数量视频生成 dit（观测实例 Wan2.2-I2V 14B，task i2v-A14B，61 帧 / 40 步）单卡推理在标称支持的分辨率下就 OOM——注意是模型标称「supported」列表里的规格（如 832×480）也塞不进单卡显存，不是超规格。
tags:
- task.debugging
- topic.diffusion
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/369
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 视频 DiT（I2V）单卡推理 OOM：降到标称之下的分辨率，或大规格转多卡序列并行

## 信号

大参数量视频生成 [dit](../../concepts/modules/dit.md)（观测实例 Wan2.2-I2V 14B，task `i2v-A14B`，61 帧 / 40 步）单卡推理在标称支持的分辨率下就 OOM——注意是模型**标称「supported」列表里**的规格（如 832×480）也塞不进单卡显存，不是超规格。

## 根因与处置

单卡显存容不下该 14B I2V 在该分辨率 / 帧数 / 步数下的推理占用。两条处置：

- **降分辨率到标称之下**：把单卡配置的 `size` 降到 640×360（≈360P，低于标称的 832×480 / 1280×720），单卡显存足以容纳，可完成单卡推理。即为塞进单卡而牺牲到标称之下的规格。
- **大规格转多卡序列并行**：更大的 1280×720 不在单卡跑，改走多卡 [ulysses](../../concepts/parallelism/ulysses.md) 序列并行（如 ulysses degree 4）。视频 DiT 接 Ulysses SP 的实现见 [video-dit-ulysses-sequence-parallel](../../optimizations/experience/rules/video_dit_ulysses_sequence_parallel.md)。

## 可迁移判断

做视频 DiT 单卡 bringup 时：别默认「标称 supported 的分辨率单卡就能跑」——大参数量 I2V 在单卡下可能需要降到标称之下的分辨率，或直接规划多卡序列并行来承接大规格。TaylorSeer 缓存 offload、量化是另两条降显存路径，见 [video-dit-taylorseer-cache-offload](../../guides/experience/interventions/video_dit_taylorseer_cache_offload.md) / [video-dit-fp8-mxfp8-quantization](../../guides/experience/interventions/video_dit_fp8_mxfp8_quantization.md)。

## 参考实现及其约束

参考 cann-recipes-infer 的 Wan2.2-I2V（`14b_single.yaml` 把 `size` 由 832×480 降到 640×360，`14b_cfg2_ulysses4.yaml` 保持 1280×720 走 ulysses4）。源未指明具体 Atlas 型号 / HBM 容量，故不外推「640×360 是单卡最大可行规格」（源只说 360P 可跑）。规格与卡数选择随 SoC / HBM 而变。

## Evidence

- `diff 事实` + `维护者确认`：`14b_single.yaml` `832*480 → 640*360`、`14b_cfg2_ulysses4.yaml` 保留 `1280*720` + ulysses4 为读到的实际 merged diff；维护者答复「过大规格单卡会 OOM，选择 360P 可以完成单卡推理」。
- 溯源下探：[cann-recipes-infer-pr-369-fix-add-hyvideo-sparse-parameters-update-readme-and-fix-sana-video-weigh](https://gitcode.com/cann/cann-recipes-infer/merge_requests/369)

<!-- cannbot:related:start -->
## 相关

- [Ulysses Sequence Parallelism](../../concepts/parallelism/ulysses.md)（`related`）：**大规格转多卡序列并行**：更大的 1280×720 不在单卡跑，改走多卡 ［ulysses］(../../concepts/parallelism/ulysses.md) 序列并行（如 ulysses degree 4）。；Ulysses 是面向**长序列多头注意力**的序列并行策略：在 attention 以外的部分沿 S（sequence）维度切分，在 attention 处通过一次 all-to-all 把切分维度从 S 换到 N（num_heads），attention 内部按 head 并行、attention 输出再 all-to-all 换回 S。runbook 给出 OOM 时的多卡分支，概念卡解释该分支如何沿序列均摊显存。
- [Wan2.2-I2V](../../concepts/models/wan2_2_i2v.md)（`related`）：“部署经统一拉起架构 ［mm-inference-launch］(../frameworks/mm_inference_launch.md)：`models/wan2.2-i2v/infer.sh` + YAML 场景切换（统一拉起 refactor，commit 06656b0，晚于上文融合算子内容钉定的 2f82d10）。config 变体（`config/`）：`14b_single`（单卡基线，`dit_cache.method` 注释切 NoCache/FBCache/TeaCache）、`14b_cfg2_ulysses4`（8 卡，CFG2 × Ulysses4 + VAE 并行 + DiT/T5 FSDP，多卡侧固定 NoCache）。”与“单卡显存容不下该 14B I2V 在该分辨率 / 帧数 / 步数下的推理占用。两条处置：”。模型卡给出单卡和 ulysses4 配置，Runbook 解释 14B 单卡 OOM 时降分辨率或转多卡的处置。
- [视频 DiT TaylorSeer 特征缓存 NPU OOM：offload 到 Host + 预取搬算并行；Host 内存成新瓶颈](../../guides/experience/interventions/video_dit_taylorseer_cache_offload.md)（`related`）：TaylorSeer 缓存 offload、量化是另两条降显存路径，见 ［video-dit-taylorseer-cache-offload］(../../guides/experience/interventions/video_dit_taylorseer_cache_offload.md) / ［video-dit-fp8-mxfp8-quantization］(../../guides/experience/interventions/video_dit_fp8_mxfp8_quantization.md)。；offload 把 `(n+1)×81.4GB` 导数搬到 CPU，**主机内存成为新瓶颈**：`720*1280*129` 规格下开启需保证 **≥400GB CPU 内存**（单卡与 8 卡 SP 变体均标注此门槛）。前者把 offload 列为 OOM 处置分支，后者给出该分支的搬运机制和 Host 内存门槛。
- [长序列视频 DiT 接 Ulysses 序列并行（pad_freqs 补齐 + world_size 拓扑校验两处易错）](../../optimizations/experience/rules/video_dit_ulysses_sequence_parallel.md)（`related`）：多卡拓扑要求“world_size == cfg_degree × sp_degree × tp_degree”，单卡 OOM 处置建议“大规格转多卡序列并行”。规则卡提供拓扑整除硬约束，Runbook 把单卡 OOM 的大规格处置指向多卡 Ulysses，可从故障信号落到正确配置。
<!-- cannbot:related:end -->
