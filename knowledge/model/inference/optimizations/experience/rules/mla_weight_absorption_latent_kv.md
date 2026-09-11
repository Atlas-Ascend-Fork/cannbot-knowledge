---
type: Optimization
title: MLA 访存 / 显存优化：优先权重吸收（absorb）+ latent-KV 缓存；稀疏 / 长序列 prefill 选 Absorb+Sparse
description: MLA 访存 / 显存优化：优先权重吸收（absorb）+ latent-KV 缓存；稀疏 / 长序列 prefill 选 Absorb+Sparse。在昇腾上做 mla 架构注意力，尤其是稀疏 / 长序列、访存主导的场景（KV 搬运是瓶颈、单卡 KV 显存吃紧）。两个 MLA 专属手段直接降访存 / 显存：权重吸收（absorb）把逐 head 的 GEMV 变成 GEMM 并砍掉 headnum 倍离散访存；latent-KV 缓存只存压缩低秩 latent、把 MHA 展开缓存的显存砍掉一半以上。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/6
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/348
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MLA 访存 / 显存优化：优先权重吸收（absorb）+ latent-KV 缓存；稀疏 / 长序列 prefill 选 Absorb+Sparse

## 适用场景

在昇腾上做 [mla](../../../concepts/modules/mla.md) 架构注意力，尤其是**稀疏 / 长序列、访存主导**的场景（KV 搬运是瓶颈、单卡 KV 显存吃紧）。两个 MLA 专属手段直接降访存 / 显存：权重吸收（absorb）把逐 head 的 GEMV 变成 GEMM 并砍掉 headnum 倍离散访存；latent-KV 缓存只存压缩低秩 latent、把 MHA 展开缓存的显存砍掉一半以上。

## 优先走权重吸收（absorb）而非 Naive 逐 head

- **Naive（MHA 计算模式）**：headnum 轴当 batch，计算时只能外抛为 for 循环；对应 BMM 的 M 轴为 1，属 GEMV，矩阵乘效率低，且有 headnum 倍的离散访存。
- **Absorb（GQA 计算模式）**：headnum 轴可转化为 matmul 的 m 轴，M=128 走 GEMM；相比 Naive 少 headnum 倍离散访存、gemv→gemm 对计算更友好。
- 结论：考虑 matmul 计算效率与离散访存，MLA 架构**都建议走权重吸收变换**；在稀疏场景下 absorb 的访存量与计算效率都更优。
- 边界：absorb 并非零代价——在稀疏 prefill 的对照中 absorb 相对 Naive+Sparse **计算量增加约 3 倍**，其优势建立在长序列 / 稀疏这类访存主导场景；纯计算主导、短序列需另行权衡。存在一个「chunk MHA vs 权重吸收 MLA」的临界点：稀疏化后选取的 kv token 数小于该临界点时走权重吸收，超过时 chunk MHA 可能更有竞争力（临界点数值未披露）。

## 稀疏 prefill 的三方案对照：选 Absorb + Sparse

稀疏化后每个 q token 只与 TopK（= min(实际序列长度, 例 2048)）个 kv token 算 Attention，prefill MLA 计算流有三种候选，决定性因素是访存：

- **方案一 Naive + Sparse Mask**：与全量 Attention 同计算量，拿不到稀疏收益，长序列性能不佳。
- **方案二 Naive + Sparse Attention**：BMM 计算量相对全量减小（如 64K/2048=32 倍），但 BMM 的 M 轴为 1（GEMV 低效），且 HBM 访存量相较全量 Attention **激增约 2048 倍**（每 token 都要把 2048 个 kv 的 K/V 重新从 HBM 读进来），访存瓶颈严重。
- **方案三 Absorb + Sparse Attention（推荐）**：相对方案二计算量增约 3 倍，但 BMM 的 M 轴变为 128（GEMM 友好），HBM 访存量相较方案二降几十倍，且与 decode 的 MLA 计算流归一（同一套 absorb 计算流，简化融合 kernel 设计）。

即：以 ~3 倍计算量换「M=128 GEMM 友好 + HBM 访存量相对方案二降几十倍」，在访存主导的长序列上整体更优。

## latent-KV 缓存布局（只存压缩 latent，勿存展开 K/V）

MHA 展开缓存显存大；MLA 只需缓存低秩 latent。每 token / 层只存 `kv_lora_rank + qk_rope_head_dim` 维压缩 latent（如 `512 + 64 = 576` 维），配合分页（paged）分块：

- 注册两块 block-paged cache：`cache_nope`（dim=`kv_lora_rank`）与 `cache_rope`（dim=`qk_rope_head_dim`），`block_size=128`、`cache_mode=PA_NZ`；`pa_max_length = input_max_len + max_new_tokens` 且须为 block_size 整数倍。
- **Prefill 走非 absorb**（`NTD_TND`）：写 cache 后用 absorb 权重把 latent 展开成 full K/V 喂 [fused-infer-attention-score](../../../concepts/kernels/fused_infer_attention_score.md)；`actual_seq_lengths` 用**累积偏移**（B>1 时用 per-request 值会跨请求边界产垃圾 token）。
- **Decode 走 absorb**（`BSND_NBSD`）：`q_nope @ kv_b_proj_w_k`，FIA 以 `key=value=cache_nope`、`key_rope=cache_rope` 计算，输出再 `@ kv_b_proj_w_v` 还原 `v_head_dim`。

参考落地把每 token/层缓存从展开的 1280 维降到 576 维（约 −55%）、128 token 输出与基线逐字匹配（仓自报）。

## 参考实现及其约束（易踩点）

参考 cann-recipes-infer 的 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md)（DSA prefill 三方案选型）与 LongCat-Flash-Lite（latent-KV paged 实现）：

- `init_absorb_weights()` 把 `kv_b_proj.weight` 预拆成 `kv_b_proj_w_k` / `kv_b_proj_w_v`，**必须在权重转置 / NZ 化之前调用**（否则原始 `(out_features, in_features)` 布局被破坏、切不出来）；`.T` 后须 `.contiguous()`。
- **Decode absorb 路径缺 MLA KV LoRA 缩放会掉精度**：FA 前对 latent 应用 `mla_scale_kv_lora=(hidden/kv_lora_rank)**0.5`。
- MLA-prolog + zigzag-CP prefill 的两段式 KV 写另有坑，见 [mla-prolog-zigzag-cp-kv-write](mla_prolog_zigzag_cp_kv_write.md)；上 C8（int8 latent）的算子接线见 [mla-c8-int8-kv-cache-op-wiring](mla_c8_int8_kv_cache_op_wiring.md)；DSA decode 的完整显存构成见 [dsa-decode-memory-budget-indexer-cache](../cases/dsa_decode_memory_budget_indexer_cache.md)。倍数（2048× / 32× / ~3× / −55%）为文档披露的 shape 分析值，非独立复测。

## 相关经验

- 另见 [DSA 稀疏 Prefill 的 MLA 计算流按序列长度选型：短序列走 MHA+Mask、长序列走 Absorb+Sparse](dsa_sparse_prefill_mla_scheme_by_seqlen.md)。


## Evidence

- `doc 披露` + `维护者确认`（@2c45117）：MLA Naive vs Absorb 三张 BMM shape 表（方案二 M=1 / 方案三 M=128）、「MLA 架构建议走权重吸收」「稀疏场景 absorb 访存与计算效率都更优」、TopK=min(seq,2048)、MHA/GQA·GEMV/GEMM 映射。
- `diff 事实`（@8fd8db72）：`cache_entries` 两块 dim=512/64、`init_absorb_weights` 拆分 + `.contiguous()`、prefill `NTD_TND` + 累积偏移 `actual_seq_lengths`、decode `BSND_NBSD` absorb、`mla_scale_kv_lora`、`pa_config`。576 维 / −55% / 1280 baseline 为仓自报。
- 溯源下探：
  - [cann-recipes-infer-issue-6-requirement-npu-deepseek-v3-2-exp-mla](https://gitcode.com/cann/cann-recipes-infer/issues/6)
  - [cann-recipes-infer-pr-348-feat-add-longcat-flash-lite-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/348)