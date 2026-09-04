---
type: Optimization
title: 把注意力映射到昇腾 FIA：attention sink / 滑窗 / 全窗的 sparse_mode 选择 + 推理 FIA vs 训练 FA + GQA 头数
description: 把注意力映射到昇腾 FIA：attention sink / 滑窗 / 全窗的 sparse_mode 选择 + 推理 FIA vs 训练 FA + GQA 头数。在昇腾上把各类注意力（含 attention sink、滑动窗口、全窗因果）落到融合算子时，优先整段映射到 FIA（npu_fused_infer_attention_score / _v2），用 sparse_mode + 入参承接各种注意力变体，而不是在 softmax 前后手拼逻辑。
tags:
- task.optimization
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/195
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/408
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/232
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/2465
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 把注意力映射到昇腾 FIA：attention sink / 滑窗 / 全窗的 sparse_mode 选择 + 推理 FIA vs 训练 FA + GQA 头数

## 条件 → 优先怎么映射

在昇腾上把各类注意力（含 attention sink、滑动窗口、全窗因果）落到融合算子时，优先整段映射到 [FIA](../../../concepts/kernels/fused_infer_attention_score.md)（`npu_fused_infer_attention_score` / `_v2`），用 `sparse_mode` + 入参承接各种注意力变体，而不是在 softmax 前后手拼逻辑。

## attention sink + 滑窗/全窗交替 → 单个 FIA

带 attention sink（每头一个可学习标量）+ 滑窗/全窗逐层交替的注意力，整段映射到单个 FIA：

- **sink 直接经 `learnable_sink` 入参承接**，无需在 softmax 前后手拼 sink logits；
- **滑窗层**用 `sparse_mode=4`（band 因果）+ `pre_tokens=sliding_window` 限回看窗口；
- **全窗层**用 `sparse_mode=3`（标准因果）；
- prefill 与 decode 复用同一调用、支持图模式。

## sparse_mode 按层类型 + 阶段选（滑窗模型）

在 FIA 上部署滑动窗口注意力：

- **滑窗层**：prefill 与 decode **都走 `sparse_mode=4`**（band 因果）并把 `pre_tokens` 设为窗口大小；
- **全注意力层**：prefill 用 `sparse_mode=3`（标准因果）、decode 用 `sparse_mode=0`（无稀疏）。

（两条 claim 对滑窗层 prefill 的取值一致为 `sparse_mode=4`；全窗层 decode 无稀疏。）

## MLA decode 收敛到单个 FIA：`input_layout` 三态 + SpecDecoding 专属 sparse_mode=3

把 MLA（latent 注意力）的 decode 路径收敛到**单个** FIA 调用时，`input_layout` 与 `sparse_mode` 要随注意力状态取三态，不再走「按 env 门控在多头 latent attention / paged-attention-mla 之间分叉 + 手工 cat」的老路。这是 MLA decode 独立于滑窗/sink 的另一类 FIA 映射场景（普通自回归 decode + 投机解码 decode 共用一个算子）。

**q/k 的 nope 与 rope 分两路传、不 cat**：`query`=q_nope、`query_rope`=q_pe；`key`=k_nope、`key_rope`=k_pe（key/value 同传 k_nope）。nope 与 rope 部分交给 FIA 内部处理，无需在算子外拼接。

**`input_layout` 三态**：

- **普通 decode**：`BNSD`。q 视图 `[num_tokens, num_heads, 1, dim]`，k 视图 `[-1, num_kv_heads, block_size, dim]`。
- **kv-cache NZ 布局**（`enable_kv_nz`）：`BSND`。q 视图 `[num_tokens, 1, num_heads, dim]`；k_nope/k_pe 要 reshape 成带 16 对齐末维的 5D（`[-1, num_kv_heads, kv_lora_rank//16, block_size, 16]` / `[-1, num_kv_heads, qk_rope_head_dim//16, block_size, 16]`）。
- **SpecDecoding（投机解码）**：`TND`（`[bs*q_seq_len, num_heads_per_rank, dim]`）。q_nope/q_pe 视图 `[num_tokens, num_heads, -1]`。

**SpecDecoding 专属参数**（区别于普通 decode 的关键）：

- `sparse_mode=3`（标准因果），配 `atten_mask=decode.attn_mask`；
- 必须传 `actual_seq_lengths=actual_seq_lengths_q`（每请求的 query 段长，投机解码一步验证多 token）；
- 前置约束 `num_tokens % spec_token_num == 0`（不满足即 assert 失败）。
- **非 spec 路径**：`sparse_mode=0`、`atten_mask=None`、`actual_seq_lengths=None`。

**paged 与后处理**：paged 承接靠 `block_table` + `block_size`（= kv_cache 第 1 维）+ `actual_seq_lengths_kv=seq_lens_list`；FIA 输出仍是 latent 维（`kv_lora_rank`），后面再接一个 V 上投影（把 latent 展回 value 头维）才得最终 attn 输出，o_proj 通常挪到 forward 末端统一做。

> 边界：这里的 `sparse_mode=3` 语义与上文滑窗/全窗场景一致（标准因果），但**触发点不同**——上文全窗层 decode 用 `sparse_mode=0`，MLA 投机解码 decode 反而用 `sparse_mode=3` 因为一步要因果地验证多个草稿 token。`input_layout` 三态与 NZ 5D reshape、`spec_token_num` 整除约束系于该参考实现（vllm-ascend MLA + DeepSeek 系），是参考实现的限制、非 FIA 算子本身的限制。

## 推理路径用推理 FIA、不用训练 FA；GQA 头数别退化

- 昇腾推理路径的自定义注意力应调用**推理专用 FIA**（`torch_npu.npu_fused_infer_attention_score`），**而非训练向 FA**（`torch_npu.npu_fusion_attention`）。
- 迁移时 **GQA/MQA 场景必须显式传 `num_key_value_heads`**（从 K 张量的头维推导），否则 KV 头数会退化为 query 头数、导致语义错误。

## 风险 / 边界

- `sparse_mode` 语义/编号系于 FIA 算子版本；跨版本迁移前核对。
- 「推理用 FIA / 训练用 FA」是因果 decode 场景的取向；DiT 类**全量非因果** cross-attention 反而用 `npu_fusion_attention`（见相关经验），别一刀切。

## 相关经验

- MLA decode 收敛到单 FIA 的 latent 注意力机制见概念页 [mla](../../../concepts/modules/mla.md)。
- FIA 的 `actual_seq_lengths_kv` 类型随后端不同见 [fia-actual-seq-lengths-kv-backend-type](../../../runbooks/runtime/fia_actual_seq_lengths_kv_backend_type.md)。
- DiT 全量非因果注意力用 npu_fusion_attention 的 BNSD 约定见 [upstream-dit-video-monkeypatch-npu-adaptation](../../../guides/experience/interventions/upstream_dit_video_monkeypatch_npu_adaptation.md)。
- 迁 TND 布局的 FIA 调用约定见 [attention-compressor-tnd-layout-migration](attention_compressor_tnd_layout_migration.md)。
- 另见 [复用共享融合算子/量化方法到不同结构模型时的静默规格失配（MoE 默认 SiLU 遇 GEGLU、钳位 SwiGLU 需专用算子、mxfp8 Linear 丢 dense 的 bias）](../../../runbooks/runtime/shared_fused_op_default_spec_mismatch.md)。
- 另见 [块内双向注意力（掩码扩散 / DLLM 解码）走 FIA 非因果全注意力，勿套 causal FA 快路径](bidirectional_attention_fia_non_causal_full.md)。
- 另见 [单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate](staged_single_card_optimize_pipeline.md)。

## Evidence

- `diff 事实`（@f8e36fc）：sink 经 `learnable_sink`、滑窗 `sparse_mode=4`+`pre_tokens`、全窗 `sparse_mode=3`、prefill/decode 复用、支持图模式。
- `diff 事实`（@8721be4）：滑窗层 prefill/decode `sparse_mode=4`+pre_tokens=window，全窗 prefill `sparse_mode=3`/decode `sparse_mode=0`。
- `diff 事实`（@ef1d890）：用推理 FIA 非训练 FA，GQA 须传 `num_key_value_heads`。
- `diff 事实`（@c8d1df3，vllm-ascend `vllm_ascend/attention/mla_v1.py`，merged 2025-08-28）：MLA `_forward_decode` 统一收敛到单个 FIA；`input_layout` 三态 BNSD/BSND(`enable_kv_nz`)/TND(SpecDecoding)；SpecDecoding 用 `sparse_mode=3`+`actual_seq_lengths=actual_seq_lengths_q`+`atten_mask=decode.attn_mask`、约束 `num_tokens % spec_token_num == 0`；非 spec `sparse_mode=0`/`atten_mask=None`；q/k 的 nope 与 rope 经 `query`/`query_rope`、`key`/`key_rope` 分传不 cat；输出 latent 维后接 V 上投影。
- 溯源下探：[cann-recipes-infer-pr-195-feat-add-gpt-oss-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/195)、[cann-recipes-infer-pr-408-feat-add-gemma-4-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/408)、[cann-recipes-infer-pr-232-fix-hunyuanimage-3-0-fix-path-error-and-fia](https://gitcode.com/cann/cann-recipes-infer/merge_requests/232)、[vllm-ascend-pr-2465-refactor-wip-refactor-mla-v1-by-moving-all-mla-preprocessing-ops-into-ml](https://github.com/vllm-project/vllm-ascend/pull/2465)

<!-- cannbot:related:start -->
## 相关

- [Gemma-4-26B-A4B](../../../concepts/models/gemma4_26b_a4b.md)（`related`）：Gemma-4 滑窗层的 Prefill/Decode 使用 sparse_mode=4 和滑窗大小；全窗层按阶段选择因果或全窗模式。
- [npu_fused_infer_attention_score (v1 / v2)](../../../concepts/kernels/fused_infer_attention_score.md)（`related`）：在昇腾上把各类注意力（含 attention sink、滑动窗口、全窗因果）落到融合算子时，优先整段映射到 ［FIA］(../../../concepts/kernels/fused_infer_attention_score.md)（`npu_fused_infer_attention_score` / `_v2`），用 `sparse_mode` + 入参承接各种注意力变体，而不是在 softmax 前后手拼逻辑。；昇腾推理侧的通用 FlashAttention 融合算子（简称 **FIA**），覆盖 Softmax-Attention 的主体计算：`softmax(QKᵀ/√d)·V`，支持 Paged KVCache、Block-Table、分离的 NoPE/RoPE Query/Key 输入、以及 Query / Key / Value 三端的动态 Int8 反量化（dequant_scale_*）。；优化卡给出 sparse_mode、sink 与滑窗的参数映射，概念卡提供被调用 FIA 的主体计算、分页与量化能力合同。
- [上游 DiT/视频生成模型搬昇腾：运行时 monkey-patch 层替代 fork + 版本门控融合算子替换](../../../guides/experience/interventions/upstream_dit_video_monkeypatch_npu_adaptation.md)（`related`）：其中「全量非因果注意力（如 cross-attention）→ `npu_fusion_attention`」有一套**可跨模型复用的 BNSD 调用约定**（哨兵 token 数 + mask 布尔化链）。；DiT 全量非因果注意力用 npu_fusion_attention 的 BNSD 约定见 ［upstream-dit-video-monkeypatch-npu-adaptation］(../../../guides/experience/interventions/upstream_dit_video_monkeypatch_npu_adaptation.md)。；非因果 DiT 分支需遵守上述 BNSD 调用约定，避免误套因果 FIA 路线。
- [单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate](staged_single_card_optimize_pipeline.md)（`related`）：# 单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate；在昇腾上把各类注意力（含 attention sink、滑动窗口、全窗因果）落到融合算子时，优先整段映射到 ［FIA］(../../../concepts/kernels/fused_infer_attention_score.md)（`npu_fused_infer_attention_score` / `_v2`），用 `sparse_mode` + 入参承接各种注意力变体，而不是在 softmax 前后手拼逻辑。。三阶段流程要求先替换 FA/FIA 融合算子，候选给出 attention sink、滑窗和全窗因果映射到 FIA 时的 sparse_mode 与入参承接原则，补充第一阶段的具体算子落地。
- [块内双向注意力（掩码扩散 / DLLM 解码）走 FIA 非因果全注意力，勿套 causal FA 快路径](bidirectional_attention_fia_non_causal_full.md)（`related`）：**把双向注意力改路由到 ［FIA］(../../../concepts/kernels/fused_infer_attention_score.md) 的「全（非因果）注意力」路径**：核心开关是 `atten_mask=None`（无 causal mask → 块内全连接）。；在昇腾上把各类注意力（含 attention sink、滑动窗口、全窗因果）落到融合算子时，优先整段映射到 ［FIA］(../../../concepts/kernels/fused_infer_attention_score.md)（`npu_fused_infer_attention_score` / `_v2`），用 `sparse_mode` + 入参承接各种注意力变体，而不是在 softmax 前后手拼逻辑。；第一张规则确定双向块的 atten_mask=None 分支，第二张规则确定滑窗、全窗和投机解码的 sparse_mode 分支，联合使用可完成注意力数学语义到 FIA 参数的互斥选路。
- [把注意力/compressor 算子迁到 TND packed-sequence 的调用约定（合轴 query、actual_seq_qlen、dequant_scale 同轴、按阶段切布局）](attention_compressor_tnd_layout_migration.md)（`related`）：“只有 `npu_fused_infer_attention_score_v2` 支持 TND_NTD”给出 TND 迁移的版本门槛；“`input_layout` 与 `sparse_mode` 要随注意力状态取三态”说明 MLA decode 统一 FIA 后仍要按普通、NZ 与投机解码选择布局和稀疏模式。
<!-- cannbot:related:end -->
