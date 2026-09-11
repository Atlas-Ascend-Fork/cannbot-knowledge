---
type: Optimization
title: 长序列视频 DiT 接 Ulysses 序列并行（pad_freqs 补齐 + world_size 拓扑校验两处易错）
description: 长序列视频 DiT 接 Ulysses 序列并行（pad_freqs 补齐 + world_size 拓扑校验两处易错）。dit 去噪主干处理很长的 video latent（如 1280×720×81 帧），单卡放不下 / 想摊时延时：接 ulysses 序列并行——沿序列维把 latent 切到各 rank、每 rank 只算自己那段过全部 block，注意力走 all-to-all 长上下文后端保跨分片完整。本经验落地于 wan2.2-i2v（Atlas A2）。HunyuanVideo 上 8 卡 Ulysses 的加速数据见 dit-step-cache-fbcache-teacache 的优化基准。
tags:
- task.optimization
- topic.diffusion
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/49
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# 长序列视频 DiT 接 Ulysses 序列并行（pad_freqs 补齐 + world_size 拓扑校验两处易错）

## 条件 → 优先尝试

[dit](../../../concepts/modules/dit.md) 去噪主干处理很长的 video latent（如 1280×720×81 帧），单卡放不下 / 想摊时延时：接 [ulysses](../../../concepts/parallelism/ulysses.md) 序列并行——沿序列维把 latent 切到各 rank、每 rank 只算自己那段过全部 block，注意力走 all-to-all 长上下文后端保跨分片完整。本经验落地于 [wan2.2-i2v](../../../concepts/models/wan2_2_i2v.md)（Atlas A2）。HunyuanVideo 上 8 卡 Ulysses 的加速数据见 [dit-step-cache-fbcache-teacache](dit_step_cache_fbcache_teacache.md) 的优化基准。

## 做什么

- `sp_dit_forward`：在 patch/时间/文本嵌入后沿序列维 `dim=1` 用 `torch.chunk(x, sp_world_size, dim=1)[sp_rank]` 切片，每 rank 只算自己那段过全部 blocks；`head` 后 `get_sp_group().all_gather(x, dim=1)` 复原全序列再 unpatchify。
- `sp_attn_forward`：把 q/k/v 交给 `xFuserLongContextAttention`（yunchang / xFuser，做 Ulysses all-to-all），保注意力跨分片完整。

依据：序列维切分让每卡只算 `1/sp` 的 token 与注意力，长序列显存/时延随卡数摊薄；all-to-all 保注意力完整。

## 两条易错约束（反例）

1. **RoPE + SP 的必配步**：freqs 须先 `pad_freqs` 补齐到 `s × sp_size`，再按 rank 取分片——**不补齐会与 chunk 后的 token 分片对不齐、位置编码错位**。
2. **拓扑硬校验**：`initialize_model_parallel` 校验 `world_size == cfg_degree × sp_degree × tp_degree`，不等即 raise（面向用户即 `nproc_per_node == cfg_size × ulysses_size`）；SP 度必须整除进 world_size。改 `--size` / `--frame_num` 改变序列长度但**不改**此约束。

## Correctness / 风险 / rollback

- 正确性锚点：`all_gather(dim=1)` 复原后再 unpatchify；freqs 分片须与 token 分片同源（先 pad 后切）。
- 无 before→after 独立复测数字（本页手段与约束为代码事实）。
- rollback：`sp_degree=1`（单卡序列）关闭 SP。

## 相关经验

- 另见 [视频 DiT（I2V）单卡推理 OOM：降到标称之下的分辨率，或大规格转多卡序列并行](../../../runbooks/performance/video_dit_single_card_oom_resolution.md)。
- 另见 [多卡 Ring/序列并行注意力用异步 all-gather + 本地 FA + LSE 合并掩盖 KV 通信](../../../guides/experience/interventions/ring_attention_comm_compute_overlap_lse_merge.md)。
- 另见 [混合序列并行 (Ulysses + Ring) 下 joint / 文本 token 的 attention 精度](../../../runbooks/precision/precision_hybrid_sp_joint_token_attention.md)。


## Evidence

- **代码事实**（clone `@4ba28799523c`）：`models/Wan2.2-I2V/wan/distributed/sequence_parallel.py` 的 `sp_dit_forward`（chunk-by-seq + head 处 `all_gather(dim=1)`）、`sp_attn_forward`（`xFuserLongContextAttention`）、`pad_freqs`；`parallel_mgr.py::initialize_model_parallel` 的 `world_size == cfg×sp×tp` 校验。
- **仓自报归因**：SP 前向为本仓自著（Adapted from Wan2.2, Copyright Huawei），并行组管理移植自 MindIE/Wan2.2。
- 溯源下探：[cann-recipes-infer-pr-49-feat-add-wan2-2-i2v-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/49)