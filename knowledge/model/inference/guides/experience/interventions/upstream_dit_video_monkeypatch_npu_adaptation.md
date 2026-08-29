---
type: Guide
title: 上游 DiT/视频生成模型搬昇腾：运行时 monkey-patch 层替代 fork + 版本门控融合算子替换
description: 上游 DiT/视频生成模型搬昇腾：运行时 monkey-patch 层替代 fork + 版本门控融合算子替换。把一个上游持续更新的开源扩散/DiT 模型（如 DiT 生成模型）搬上昇腾，且不想把上游源码 fork 进仓再手改（fork 会让上游更新变成痛苦的 rebase）时，用运行时 monkey-patch 层做零侵入适配。
tags:
- task.debugging
- topic.attention
- topic.diffusion
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/341
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# 上游 DiT/视频生成模型搬昇腾：运行时 monkey-patch 层替代 fork + 版本门控融合算子替换

## 适用场景

把一个**上游持续更新的开源扩散/DiT 模型**（如 [DiT](../../../concepts/modules/dit.md) 生成模型）搬上昇腾，且不想把上游源码 fork 进仓再手改（fork 会让上游更新变成痛苦的 rebase）时，用**运行时 monkey-patch 层**做零侵入适配。

## 何时不适用

- 上游改动小且稳定、直接 fork 更简单；
- 需要改的是上游数据流结构（非仅算子替换），monkeypatch 难以覆盖。

## 做什么：统一 monkey-patch 入口

用一个统一 `apply_all()` 入口，在运行时把上游模块的层/算子替换成昇腾版，对上游源码**零侵入**，上游更新只需重拉源码。要成立必须满足**三条前置约束**：

1. **patch 必须在 import 上游模块之前注入**——晚了则上游已按原实现绑定，patch 不生效；
2. **NPU 无 triton，需伪造 triton stub**——上游若 `import triton`，先注入 stub 避免 import 失败；
3. **新增的 zeros-init 补丁层必须在 `load_state_dict` 后手工同步真实权重**——否则补丁层保持零权重、输出错。

## 融合算子替换的通用做法

把上游原生小算子换成 torch_npu 融合算子时：

- **全部替换点用一个版本门控 `_npu_available` 包起来**，非 NPU / 低版本回退原实现；
- 其中「全量非因果注意力（如 cross-attention）→ `npu_fusion_attention`」有一套**可跨模型复用的 BNSD 调用约定**（哨兵 token 数 + mask 布尔化链）。注意：这里全量非因果场景用训练向 `npu_fusion_attention`（BNSD），与因果 decode 用推理 FIA 相反（见相关经验）。

## correctness 验证 / 风险 / rollback

- 每个 monkeypatch 点用 `_npu_available` 门控，非 NPU 环境自动回退原实现 = 天然 rollback。
- zeros-init 补丁层若漏同步权重 → 输出全错但不报错，须在 `load_state_dict` 后校验。
- patch 注入时机错（晚于 import）= 静默不生效，须核对入口顺序。

## 相关经验
- [aclgraph 图捕获前 monkeypatch upstream graph_captu](../../../runbooks/runtime/aclgraph_capture_patch_module_base_vs_mro.md)

- CUDA 原生 DiT/视频模型的注意力后端改路由 + 绕过 SP 库 CUDA 硬检查见 [cuda-native-dit-video-attention-sp-npu-adaptation](../../../optimizations/experience/rules/cuda_native_dit_video_attention_sp_npu_adaptation.md)。
- DiT 算子级代数改写（conv/LN 折叠）见 [dit-cnn-operator-algebraic-rewrite-npu](../../../optimizations/experience/rules/dit_cnn_operator_algebraic_rewrite_npu.md)；DiT 融合算子/autocast 精度对齐见 [precision-dit-fusion-autocast-cossin-dtype](../../../optimizations/experience/rules/precision_dit_fusion_autocast_cossin_dtype.md)。
- 因果 decode 用推理 FIA（与此处全量非因果用 FA 相对）见 [attention-to-fia-sparse-mode-sink-window](../../../optimizations/experience/rules/attention_to_fia_sparse_mode_sink_window.md)。

## Evidence

- `diff 事实`（@b300157）：统一 `apply_all()` monkeypatch 层 + 三前置（patch 先于 import / triton stub / zeros-init 层 load_state_dict 后同步）；融合算子替换用 `_npu_available` 门控、全量非因果 attn → `npu_fusion_attention` BNSD 约定。
- 溯源下探：[cann-recipes-infer-pr-341-refactor-simplify-sana-video-npu-patches](https://gitcode.com/cann/cann-recipes-infer/merge_requests/341)

<!-- cannbot:related:start -->
## 相关

- [CUDA 原生 DiT/视频生成模型移植昇腾：注意力后端改路由 NPU + 绕过 SP 库 CUDA 硬检查](../../../optimizations/experience/rules/cuda_native_dit_video_attention_sp_npu_adaptation.md)（`related`）：用一个统一 `apply_all()` 入口，在运行时把上游模块的层/算子替换成昇腾版，对上游源码**零侵入**，上游更新只需重拉源码。；侵入式改第三方库 + monkey-patch，源保留 GPU 兼容。；目标页给出 DiT 适配中可被统一入口封装的具体 monkey-patch 落点和 GPU 回退边界。
- [把注意力映射到昇腾 FIA：attention sink / 滑窗 / 全窗的 sparse_mode 选择 + 推理 FIA vs 训练 FA + GQA 头数](../../../optimizations/experience/rules/attention_to_fia_sparse_mode_sink_window.md)（`related`）：其中「全量非因果注意力（如 cross-attention）→ `npu_fusion_attention`」有一套**可跨模型复用的 BNSD 调用约定**（哨兵 token 数 + mask 布尔化链）。；DiT 全量非因果注意力用 npu_fusion_attention 的 BNSD 约定见 ［upstream-dit-video-monkeypatch-npu-adaptation］(../../../guides/experience/interventions/upstream_dit_video_monkeypatch_npu_adaptation.md)。；目标页明确把非因果 DiT 分支回指焦点页的 BNSD 合同，可避免误套因果 FIA 路线。
<!-- cannbot:related:end -->
