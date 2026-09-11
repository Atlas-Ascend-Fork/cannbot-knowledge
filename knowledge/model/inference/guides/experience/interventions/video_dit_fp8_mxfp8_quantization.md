---
type: Guide
title: 视频 DiT 量化降显存 / 带宽：per-block FP8 注意力（主要收益，Ulysses-only）+ MXFP8 matmul（跳过 adaLN）
description: 视频 DiT 量化降显存 / 带宽：per-block FP8 注意力（主要收益，Ulysses-only）+ MXFP8 matmul（跳过 adaLN）。视频 / 图像 dit 推理里 attention 与 Linear（MLP / 投影）在 bf16 下占显存与带宽，想降本时。这里有两条量化手段，优先级不同：FP8 注意力量化是端到端加速主要来源，MXFP8 matmul 量化单独收益小、主要作为叠加项。两者都需 ascend-950（Atlas 950）级 FP8 硬件（Ascend910B / Ascend910_93 抛 RuntimeError）。
tags:
- task.debugging
- topic.attention
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/325
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- '950'
---

# 视频 DiT 量化降显存 / 带宽：per-block FP8 注意力（主要收益，Ulysses-only）+ MXFP8 matmul（跳过 adaLN）

## 适用场景

视频 / 图像 [dit](../../../concepts/modules/dit.md) 推理里 attention 与 Linear（MLP / 投影）在 bf16 下占显存与带宽，想降本时。这里有两条量化手段，**优先级不同**：FP8 注意力量化是端到端加速主要来源，MXFP8 matmul 量化单独收益小、主要作为叠加项。两者都需 [ascend-950](../../../concepts/platforms/ascend_950.md)（Atlas 950）级 FP8 硬件（`Ascend910B` / `Ascend910_93` 抛 RuntimeError）。

## 手段一 · per-block FP8 注意力（主要收益）

对显存带宽受限的视频 DiT 注意力，用 per-block 动态 [fp8-attention](../../../concepts/quantization/fp8_attention.md)（E4M3）量化 Q/K/V，经 [fused-infer-attention-score](../../../concepts/kernels/fused_infer_attention_score.md) v2 的 per-block 量化模式计算：

- Q 与 K/V 用差异化 block 粒度：**Q group=128、K/V group=256**（`npu_dynamic_block_quant`）。
- 量化张量转 BNSD 后喂 FIA v2，`query/key/value_quant_mode=7`（per-block 动态量化）、per-block scale 随张量单独传入，输出回 bf16。BNSD layout 为 FIA v2 所需（docstring 披露）。
- 可对文本前缀段只走 FP8、余段走普通 FIA 再 cat。

**何时不适用（硬约束）**：FP8 FA **只支持纯 [ulysses](../../../concepts/parallelism/ulysses.md) 序列并行**——`ring_world_size > 1` 时抛 `ValueError("supports only Ulysses Attention sequence parallel")`，与 [ring-attention](../../../concepts/parallelism/ring_attention.md) 混合并行不可用。给用 Ring Attention 的模型上 FP8 FA 前须先确认并行模式为纯 Ulysses（视频 DiT 接 Ulysses 序列并行见 [video-dit-ulysses-sequence-parallel](../../../optimizations/experience/rules/video_dit_ulysses_sequence_parallel.md)）。

## 手段二 · MXFP8 A8W8 matmul（叠加项，跳过 adaLN）

对 DiT 的 `nn.Linear` 做 [mxfp8-a8w8](../../../concepts/quantization/mxfp8_a8w8.md) A8W8 量化（权重 per-group 直转 FP8、激活 per-token 动态量化）：

- **量化范围规则（可迁移核心）**：只量化 `double_blocks` / `single_blocks` 内的 `nn.Linear`；**必须跳过含 `mod` 的调制层（adaLN modulation）与任何 1D 权重**——adaLN 对精度敏感，量化会伤质量。
- 前向调用约定：激活 per-token 动态量化 + 预量化权重，`npu_quant_matmul` 用 E8M0（`float8_e8m0fnu`）缩放、权重量化组 `group_sizes=[1,1,32]`、权重 scale 以 `.permute(1,0,2)` 传入。

## 优先级 · 收益分解（950PR / HunyuanVideo 720p 129 帧，仓自报无独立复测）

单独 MXFP8 matmul 收益小（单卡 e2e 1.06x、ulysses8 1.05x）；FP8 FA 是主要来源（单卡 1.58x、ulysses8 1.32x）；两者叠加单卡 1.64x、ulysses8 1.38x。VAE 段不量化、基本持平。**量化视频 DiT 时应优先做 FP8 注意力量化，matmul 量化作叠加。** 仅陈述报告的这两组受控配置，不外推单调规律；doc 未给量化后精度 / 相似度指标。

## 参考实现及其约束

参考 cann-recipes-infer 的 HunyuanVideo（`module/fa_quant/fa_quant.py` 的 `npu_fp8_attn` / `npu_group_quant`、`hyvideo/modules/mxfp8_a8w8.py` 的 `dynamic_convert_mxfp8_linear` / `mxfp8_linear_forward`、`inference.py` 硬件门控），[ascend-950](../../../concepts/platforms/ascend_950.md)。group_size 128/256、`group_sizes=[1,1,32]`、E8M0、Ulysses-only、Atlas 950 门控为参考实现约束；「converter 当前产出 / 传入 X」不升为「算子只能吃 X」。

## Evidence

- `diff 事实`（@dfa1a889）：`fa_quant.py`（`npu_group_quant` group 128/256、`npu_fp8_attn` FIA v2 `quant_mode=7`、`ring_world_size>1` ValueError）、`mxfp8_a8w8.py`（跳过 `mod` / 1D 权重、`group_sizes=[1,1,32]` / E8M0）、`inference.py` Atlas 950 门控为读到的实际 merged diff。
- `doc 披露`（@dfa1a889）：`hunyuan_video_optimization.md` 量化结果表逐格照录（单卡 baseline 2580.87s → FP8 FA 1638.55s / +matmul 1571.24s；ulysses8 256.92s → 193.96s / 185.54s），仓自报、无独立复测。
- 溯源下探：[cann-recipes-infer-pr-325-feat-hunyuanvideo-support-fa-matmul-quant-and-uaa](https://gitcode.com/cann/cann-recipes-infer/merge_requests/325)