---
type: Optimization
title: 视频 DiT FP8 量化规则：per-block Attention 与 MXFP8 matmul
description: Atlas 950 视频 DiT 量化的显存与带宽决策：per-block FP8 注意力限定纯 Ulysses（Ulysses-only），MXFP8 matmul 跳过 adaLN 敏感层；HunyuanVideo 历史收益不外推，接入与观测分开核对。
tags:
- task.debugging
- topic.attention
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/325
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/dfa1a889e6787d03c7c535e968c694a59114182f/module/fa_quant/fa_quant.py
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/dfa1a889e6787d03c7c535e968c694a59114182f/module/unified_sp/core.py
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/dfa1a889e6787d03c7c535e968c694a59114182f/models/hunyuan-video/hyvideo/modules/mxfp8_a8w8.py
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/dfa1a889e6787d03c7c535e968c694a59114182f/models/hunyuan-video/hyvideo/inference.py
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:43:19Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - dit
      quantization:
      - fp8
---
# 视频 DiT FP8 量化规则：per-block Attention 与 MXFP8 matmul

## 适用场景

视频 / 图像 [dit](../../concepts/modules/dit.md) 推理里 attention 与 Linear（MLP / 投影）在 bf16 下占显存与带宽，想降本时。这里有Attention与matmul两条量化手段，应分别验收目标负载；HunyuanVideo的一组历史结果不规定所有模型的优先级。两者都需 [ascend-950](../../concepts/platforms/ascend_950.md)（Atlas 950）级 FP8 硬件（`Ascend910B` / `Ascend910_93` 抛 RuntimeError）。

## 手段一 · per-block FP8 注意力

对显存带宽受限的视频 DiT 注意力，用 per-block 动态 [fp8-attention](../../concepts/quantization/fp8_attention.md)（E4M3）量化 Q/K/V，经 [fused-infer-attention-score](../../concepts/kernels/fused_infer_attention_score.md) v2 的 per-block 量化模式计算：

- Q 与 K/V 用差异化 block 粒度：**Q group=128、K/V group=256**（`npu_dynamic_block_quant`）。
- 量化张量转 BNSD 后喂 FIA v2，`query/key/value_quant_mode=7`（per-block 动态量化）、per-block scale 随张量单独传入，输出回 bf16。BNSD layout 为 FIA v2 所需（docstring 披露）。
- 固定实现按 cu_seqlens 的有效边界切分：有效图像 token 与有效文本 token 的联合段走 FP8，剩余文本 padding 段走普通 FIA，最后 cat；不是将图像和文本注意力各自独立计算。

**何时不适用（硬约束）**：FP8 FA **只支持纯 [ulysses](../../concepts/parallelism/ulysses.md) 序列并行**——`ring_world_size > 1` 时抛 `ValueError("supports only Ulysses Attention sequence parallel")`，与 [ring-attention](../../concepts/parallelism/ring_attention.md) 混合并行不可用。给用 Ring Attention 的模型上 FP8 FA 前须先确认并行模式为纯 Ulysses（视频 DiT 接 Ulysses 序列并行见 [video-dit-ulysses-sequence-parallel](video_dit_ulysses_sequence_parallel.md)）。

## 手段二 · MXFP8 A8W8 matmul（跳过 adaLN）

对 DiT 的 `nn.Linear` 做 [mxfp8-a8w8](../../concepts/quantization/mxfp8_a8w8.md) A8W8 量化（权重 per-group 直转 FP8、激活 per-token 动态量化）：

- **量化范围规则（可迁移核心）**：只量化 `double_blocks` / `single_blocks` 内的 `nn.Linear`；**必须跳过含 `mod` 的调制层（adaLN modulation）与任何 1D 权重**——adaLN 对精度敏感，量化会伤质量。
- 前向调用约定：激活 per-token 动态量化 + 预量化权重，`npu_quant_matmul` 用 E8M0（`float8_e8m0fnu`）缩放、权重量化组 `group_sizes=[1,1,32]`、权重 scale 以 `.permute(1,0,2)` 传入。

## 优先级与验收

[950来源观测](../benchmark_observations/hunyuan_video_950_source_benchmark.md)保存两组结果，[接入案例](../cases/hunyuan_video_950_fp8_quantization.md)保存实现差异。在该来源配置中 FP8 Attention 收益较大；不能据此规定所有 DiT 的量化顺序。先分别对照 BF16 测量 Attention、matmul 和组合路径，再验收视频质量与端到端耗时。质量未通过或没有净收益时关闭对应量化项。

## 参考实现及其约束

参考 cann-recipes-infer 的 HunyuanVideo（`module/fa_quant/fa_quant.py` 的 `npu_fp8_attn` / `npu_group_quant`、`hyvideo/modules/mxfp8_a8w8.py` 的 `dynamic_convert_mxfp8_linear` / `mxfp8_linear_forward`、`inference.py` 硬件门控），[ascend-950](../../concepts/platforms/ascend_950.md)。group_size 128/256、`group_sizes=[1,1,32]`、E8M0、Ulysses-only、Atlas 950 门控为参考实现约束；「converter 当前产出 / 传入 X」不升为「算子只能吃 X」。

## Evidence

- `diff 事实`（@dfa1a889）：`fa_quant.py`（`npu_group_quant` group 128/256、`npu_fp8_attn` FIA v2 `quant_mode=7`、`ring_world_size>1` ValueError）、`mxfp8_a8w8.py`（跳过 `mod` / 1D 权重、`group_sizes=[1,1,32]` / E8M0）、`inference.py` Atlas 950 门控为读到的实际 merged diff。
- `doc 披露`（@dfa1a889）：来源量化结果统一链接[950观测](../benchmark_observations/hunyuan_video_950_source_benchmark.md)，仓自报、无独立复测。
- 溯源下探：[cann-recipes-infer-pr-325-feat-hunyuanvideo-support-fa-matmul-quant-and-uaa](https://gitcode.com/cann/cann-recipes-infer/merge_requests/325)
