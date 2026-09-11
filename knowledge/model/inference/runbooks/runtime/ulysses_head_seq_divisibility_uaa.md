---
type: Runbook
title: Ulysses 按 head 切分的整除约束（序列可软填充、head 需 UAA 放开）
description: Ulysses 按 head 切分的整除约束（序列可软填充、head 需 UAA 放开）。Ulysses 序列并行推理（ulysses_world_size > 1）下： 序列长不整除：视频/图像生成模型（序列长由分辨率/帧数决定、取任意值）在序列长不被 ulysses_world_size 整除时直接失败。 head 数不整除：num_heads % ulysses_world_size != 0 时直接 raise ValueError（还常附带视频 H%16%SP==0 or W%16%SP==0 之类分辨率约束）。
tags:
- task.debugging
- topic.attention
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/253
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/325
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/353
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Ulysses 按 head 切分的整除约束（序列可软填充、head 需 UAA 放开）

## 信号

[Ulysses](../../concepts/parallelism/ulysses.md) 序列并行推理（`ulysses_world_size > 1`）下：

- **序列长不整除**：视频/图像生成模型（序列长由分辨率/帧数决定、取任意值）在序列长不被 `ulysses_world_size` 整除时直接失败。
- **head 数不整除**：`num_heads % ulysses_world_size != 0` 时直接 `raise ValueError`（还常附带视频 `H%16%SP==0 or W%16%SP==0` 之类分辨率约束）。

## 触发条件 / 根因

标准 Ulysses 用 head-to-seq 的 all-to-all，**同时**把序列维和 head 维在各 rank 间等分，故两维都要求能被 `ulysses_world_size` 整除。序列长不整除→无法均分；head 数不整除→all-to-all 头切分不成立。单卡走 all-to-all no-op 分支，无此约束。

## 修法（两维方向相反，须一起记）

- **序列维 = 软约束（可软填充吸收）**：在 head-to-seq all-to-all **之前**把 Q/K/V 的序列维零填充到 `ulysses_world_size` 整数倍，seq-to-head all-to-all **之后**按原序列长切回。尾部零填充落在注意力输出的无效区间，不影响有效 token 结果。对任何"序列长任意、又要跑标准 Ulysses"的场景通用。
- **head 维 = 硬约束（须 UAA 放开，或改配置/并行度）**：不整除只能调模型配置 / Ulysses 并行度，或走 **UAA（Ulysses-Anything Attention）**——把 head 补齐到 `world_size` 整数倍再切本地片、算完 unpad：
  - **补的 head 数须 < 每卡本地 head 数**，否则拒绝（如 `h=30, ws=8` 补 2 允许；`h=30, ws=16` 补 14 被 `raise`）。
  - **各 rank 序列长动态收集**：动态 shape 下各 rank `s_local` 可不等，先 all_gather 收各 rank 实际长度（`_gather_size_by_comm`）再按 split_sizes 做 `all_to_all_single`；输出侧按各 rank 实际长度 all_gather 后 cat，而非等分。
  - **稀疏度向量按实际本地 head 数对齐**：叠加块稀疏时，不能假定各 rank 本地 head 数相等，要跨 rank 收集实际本地 head 数算出每 rank `head_start/head_end` 再切，支持不均匀切分。
  - **约束：UAA 仅支持纯 Ulysses**，不支持 Ulysses + [Ring](../../concepts/parallelism/ring_attention.md) 混合序列并行。

**取用建议**：新代码走 `--ulysses-anything` 开关统一处理任意序列长 / 任意 head 数，不必再手写前向内 pad/unpad；错误信息也会提示"用 `--ulysses-anything` 绕过头数整除限制"。

## 参考实现

模块 `module/unified_sp/core.py::UnifiedSPAttention`（`ulysses_world_size` / `ring_world_size` 两个并行度）+ `module/unified_sp/uaa.py`（`_maybe_pad_qkv_head` / all_to_all-anything / patch 对齐 split）。落地于 [HunyuanVideo](../../concepts/models/hunyuan_video.md)（head=24）、[Wan2.2-I2V](../../concepts/models/wan2_2_i2v.md) 视频 [DiT](../../concepts/modules/dit.md)。手段改自 `vipshop/cache-dit`。序列并行本体见 [video-dit-ulysses-sequence-parallel](../../optimizations/experience/rules/video_dit_ulysses_sequence_parallel.md)；与块稀疏同用见 [blockwise-sparse-attention-ulysses-integration](../../guides/experience/interventions/blockwise_sparse_attention_ulysses_integration.md)。

## 相关经验

- 另见 [多卡 MoE/SP 部署的整除·对齐约束（batch↔EP、input_max_len↔attn-TP）](parallel_dim_divisibility_constraints.md)。


## Evidence

- `diff 事实`（序列 pad/unpad，PR head @1e865ed2183c）：`UnifiedSPAttention.forward` 序列维 pad→all-to-all→切回。演进：基准 sha @2c45117d 处 `_forward_core` 已不再对序列维补齐，改由 `_all_to_all_qkv_anything` 承接任意/动态切分，头维由 `_maybe_pad_qkv_head` 补齐，头数硬约束由 `--ulysses-anything` 放宽。溯源下探：[cann-recipes-infer-pr-253-fix-fix-the-issue-where-the-sequence-length-is-not-divisible-when-ulysse](https://gitcode.com/cann/cann-recipes-infer/merge_requests/253)
- `diff 事实`（UAA head padding，@dfa1a889）：`_maybe_pad_qkv_head`（补数须 < 本地 head 数否则 `raise`）、`_gather_size_by_comm` + `all_to_all_single`、patch 对齐 split_func；UAA 仅纯 Ulysses 的约束。doc 自报 ulysses8 下 UAA-on 482.65s vs off 487.68s（额外开销可忽略，仅此配置）。溯源下探：[cann-recipes-infer-pr-325-feat-hunyuanvideo-support-fa-matmul-quant-and-uaa](https://gitcode.com/cann/cann-recipes-infer/merge_requests/325)
- `diff 事实`（稀疏场景 UAA，@a12b2affe2d0）：`_slice_ulysses_local_heads_with_uaa`（pad→slice→unpad、标准分支不整除 `raise ValueError`）、`_resolve_ulysses_local_sparsity_override`（跨 rank 收本地 head 数、非均匀切分）。溯源下探：[cann-recipes-infer-pr-353-feat-hunyuanvideo-support-ulysses-parallelism-with-block-wise-sparse-att](https://gitcode.com/cann/cann-recipes-infer/merge_requests/353)