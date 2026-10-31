---
type: Optimization
title: 昇腾推理统一 TND packed-sequence 布局：为何是标准、BSND/packed-1D shim 的等长约束与变长崩溃
description: 在 CANN Executor 适配变长请求时，保持 packed 输入的请求边界和显式长度；TND 算子路径与 BSND 适配的约束须按具体实现核对，避免等长 reshape 和末 token 选择错误。
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
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/design/packed_sequence_design.md
  role: primary
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- agnostic
---

# 昇腾推理统一 TND packed-sequence 布局：为何是标准、BSND/packed-1D shim 的等长约束与变长崩溃

## 条件 → 优先选什么

在 [cann-executor](../../concepts/frameworks/cann_executor.md) 上给模型接注意力/KV cache 时，优先采用能消费 packed 边界的 TND 算子路径。当前框架以 packed token 和长度元数据作为输入契约；模型内部可以转换其他布局，但必须保留请求边界，不能用等长 reshape 假设承载任意变长请求。

## 框架 packed 输入与模型内部布局的边界

- 历史 PR386 删除框架的非 packed 开关。当前 `packed_sequence_design.md` 区分框架的一维输入与模型内部算子布局；“框架只接受 packed”不等于所有中间张量都只能用 TND。
- dense 模型 attention 适配也统一采用 TND、与 MoE 用例对齐；维护者明确 TND 是后续标准做法。

## BSND / packed-1D 模型的 shim 及其约束

框架向模型喂 **packed-1D** 的 `input_ids`/`position_ids` 与 packed `[B*S]` 的 kv_len。BSND 布局的模型需在 forward 边界加 **reshape shim**，但该 shim 只支持：

- **等长 packed prefill**；
- **`batch_size_per_dp_rank==1` 的 decode**。

这些是上述旧 shim 的限制。变长 packed 或多序列 Decode 应使用完整保留请求边界的实现，优先选 TND；其他布局必须显式适配与验证，不能靠该 shim 承载。packed-1D 下还有几条 lm_head/判阶段约定（维护者 review 确认）：

- 当前 packed Prefill 在 token 维以 `actual_seq_lengths_cu_q - 1` 取每请求末 token，**不能用普通长度 `actual_seq_lengths_q - 1` 当累计偏移，也不能用 `max(position_ids)`**；历史 BSND shim 的轴和字段语义须单独核对；
- `view(batch_size, -1)` 的 1D→BS reshape **仅在等长 prompt 下成立**；
- 判是否 prefill 用 `forward_metadata.is_prefill`，**而非 shape/位置启发式**。

## 失败签名：等长假设的 reshape 在变长下崩

不迁 TND、强行按等长 reshape 会撞两类崩：

- **BSH reshape 假设等长 batch**：把 1D packed token 流按 `seq_len = total_tokens // batch_size` 平均 reshape 成 BSH，隐含要求同 batch 内所有请求等长；变长 prompt 会 `view` 报 shape 错，或恰好整除时把不同请求的 token 边界混在一起（更隐蔽）。
- **micro-batch 丢批主序致 cos_sin 失配**：prefill micro-batch 把 `input_ids` 展平成 `[1, total]` 再按序列长切 micro-batch，会丢掉 RoPE cos_sin 依赖的批主序 `[B, seq_len]`，cos_sin 与 q/k 形状对不上；每个 micro-batch 必须 `reshape(-1, seq_len)` 还原 `[B, seq_len]`，且多个 micro-batch 的输出要沿 **batch 维（dim=0）** 而非序列维（dim=1）拼回。

## 风险 / 边界

- shim 是过渡手段，只覆盖等长 prefill + 单序列 decode；该旧 shim 不能覆盖生产级变长 continuous-batching；其他布局适配需单独验证边界语义。
- 用 `is_prefill` 判阶段，用普通长度检查请求规模，用累计边界定位 packed 末 token；字段的完整对应关系见 [Packed Sequence 元数据](../../concepts/techniques/packed_sequence_metadata.md)。

## 相关经验
- [昇腾编码器 packed 全注意力：两个可互换融合算子的 seq_len 语义不同（unpa](../../runbooks/runtime/mm_encoder_packed_attention_seqlen_semantics.md)

- 把具体算子（FIA/compressor）迁到 TND 的调用约定见 [attention-compressor-tnd-layout-migration](attention_compressor_tnd_layout_migration.md)。
- 非打包路径的 batch 整除约束（TND 免除）见 [tp-dp-batch-and-page-sizing-constraints](../../runbooks/runtime/tp_dp_batch_and_page_sizing_constraints.md)。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/317)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/386)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/348)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/408)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/127)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/403)（evidence）
- [packed_sequence_design.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/design/packed_sequence_design.md)（primary）
