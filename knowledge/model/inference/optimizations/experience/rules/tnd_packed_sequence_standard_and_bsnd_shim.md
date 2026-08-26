---
type: Optimization
title: 昇腾推理统一 TND packed-sequence 布局：为何是标准、BSND/packed-1D shim 的等长约束与变长崩溃
description: 昇腾推理统一 TND packed-sequence 布局：为何是标准、BSND/packed-1D shim 的等长约束与变长崩溃。在 cann-executor 上给模型接注意力/KV cache 时，默认优先 TND（packed-sequence）布局，别再保留 BSH/BSND 分支。这是仓级标准；不遵从它的路径（等长假设的 reshape）在变长 continuous-batching 下会崩。
tags:
- task.optimization
- topic.attention
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/317
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/386
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/348
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/408
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/127
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/403
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 昇腾推理统一 TND packed-sequence 布局：为何是标准、BSND/packed-1D shim 的等长约束与变长崩溃

## 条件 → 优先选什么

在 [cann-executor](../../../concepts/frameworks/cann_executor.md) 上给模型接注意力/KV cache 时，**默认优先 TND（packed-sequence）布局**，别再保留 BSH/BSND 分支。这是仓级标准；不遵从它的路径（等长假设的 reshape）在变长 continuous-batching 下会崩。

## TND 是标准且唯一布局

- executor-core 把 TND（packed sequence）定为 attention 的**默认且唯一**布局——prefill 与 decode 两阶段、dense 与 MoE 模型统一走 TND，原 `packed_sequence` 开关被删除、非打包/BSH 路径不再保留。
- dense 模型 attention 适配也统一采用 TND、与 MoE 用例对齐；维护者明确 TND 是后续标准做法。

## BSND / packed-1D 模型的 shim 及其约束

框架向模型喂 **packed-1D** 的 `input_ids`/`position_ids` 与 packed `[B*S]` 的 kv_len。BSND 布局的模型需在 forward 边界加 **reshape shim**，但该 shim 只支持：

- **等长 packed prefill**；
- **`batch_size_per_dp_rank==1` 的 decode**。

**变长 packed 或多序列 decode 必须把注意力迁到 TND 布局**（不能靠 shim 硬撑）。packed-1D 下还有几条 lm_head/判阶段约定（维护者 review 确认）：

- lm_head 取每请求最后一个 token 的 hidden 须用 `torch.gather(hidden, 1, actual_seq_lengths_q - 1)`，**而非 `max(position_ids)`**（后者遇 pad 静默出错）；
- `view(batch_size, -1)` 的 1D→BS reshape **仅在等长 prompt 下成立**；
- 判是否 prefill 用 `forward_metadata.is_prefill`，**而非 shape/位置启发式**。

## 失败签名：等长假设的 reshape 在变长下崩

不迁 TND、强行按等长 reshape 会撞两类崩：

- **BSH reshape 假设等长 batch**：把 1D packed token 流按 `seq_len = total_tokens // batch_size` 平均 reshape 成 BSH，隐含要求同 batch 内所有请求等长；变长 prompt 会 `view` 报 shape 错，或恰好整除时把不同请求的 token 边界混在一起（更隐蔽）。
- **micro-batch 丢批主序致 cos_sin 失配**：prefill micro-batch 把 `input_ids` 展平成 `[1, total]` 再按序列长切 micro-batch，会丢掉 RoPE cos_sin 依赖的批主序 `[B, seq_len]`，cos_sin 与 q/k 形状对不上；每个 micro-batch 必须 `reshape(-1, seq_len)` 还原 `[B, seq_len]`，且多个 micro-batch 的输出要沿 **batch 维（dim=0）** 而非序列维（dim=1）拼回。

## 风险 / 边界

- shim 是过渡手段，只覆盖等长 prefill + 单序列 decode；生产级变长 continuous-batching 必须端到端 TND。
- 判 prefill/等长/取末 token 一律用显式 metadata（`is_prefill` / `actual_seq_lengths_q`），不用 shape 启发式。

## 相关经验
- [昇腾编码器 packed 全注意力：两个可互换融合算子的 seq_len 语义不同（unpa](../../../runbooks/runtime/mm_encoder_packed_attention_seqlen_semantics.md)

- 把具体算子（FIA/compressor）迁到 TND 的调用约定见 [attention-compressor-tnd-layout-migration](attention_compressor_tnd_layout_migration.md)。
- 非打包路径的 batch 整除约束（TND 免除）见 [tp-dp-batch-and-page-sizing-constraints](../../../runbooks/runtime/tp_dp_batch_and_page_sizing_constraints.md)。

## Evidence

- `diff 事实 / 维护者确认`（@2c45117）：executor-core TND 为默认且唯一布局、删 packed_sequence 开关（PR 描述 + diff）。
- `维护者确认`（@9a50738）：dense attention 统一 TND、TND 为后续标准。
- `diff 事实 / 维护者确认`（@8fd8db7）：packed-1D lm_head 用 gather、view 仅等长成立、判 prefill 用 is_prefill。
- `diff 事实`（@8721be4）：BSND shim 只支持等长 prefill + bs==1 decode，变长/多序列须迁 TND。
- `diff 事实`（@3c3ca0b / @f7e80e5）：micro-batch 需 reshape 还原 [B,seq_len] 且沿 dim=0 拼；BSH 平均 reshape 假设等长。
- 溯源下探：[cann-recipes-infer-pr-317-feat-infer-supports-qwen3-8b](https://gitcode.com/cann/cann-recipes-infer/merge_requests/317)、[cann-recipes-infer-pr-386-refactor-use-packed-sequence-by-default-kv-cache-add-page-attention](https://gitcode.com/cann/cann-recipes-infer/merge_requests/386)、[cann-recipes-infer-pr-348-feat-add-longcat-flash-lite-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/348)、[cann-recipes-infer-pr-408-feat-add-gemma-4-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/408)、[cann-recipes-infer-pr-127-fix-cos-sin-shape-problem](https://gitcode.com/cann/cann-recipes-infer/merge_requests/127)、[cann-recipes-infer-pr-403-feat-adapt-and-optimize-hy3-preview-inference-via-deepseek-v4-pro-recipe](https://gitcode.com/cann/cann-recipes-infer/merge_requests/403)
