---
type: Optimization
title: MLA-prolog + zigzag-CP Prefill 必须用两段式 KV cache 写（勿按 slot_mapping 直写 paged cache）
description: 结构为 mla-prolog（算子 torch.ops.custom.npu_mla_prolog_v3）+ paged KV cache（kv-cache-manager）的 Prefill，且叠加了 zigzag-cp（CP 仅在 prefill 生效，与长上下文 input_max_len 16384/32768 搭配）时：不能让 prolog 算子按 slot_mapping 直写最终 paged cache，必须改成两段式 KV 写。覆盖 kv_cache_quant_mode ∈ {int8(C8), 非量化}，证据来自 deepseek-v3.2-exp。这是把 long-seq-prefill-context-parallel 落到 MLA-prolog 上时的一处必配正确性细节。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/197
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MLA-prolog + zigzag-CP Prefill 必须用两段式 KV cache 写（勿按 slot_mapping 直写 paged cache）

## 条件 → 优先怎么写

结构为 [mla-prolog](../../../concepts/kernels/mla_prolog.md)（算子 `torch.ops.custom.npu_mla_prolog_v3`）+ paged KV cache（[kv-cache-manager](../../../concepts/frameworks/kv_cache_manager.md)）的 **Prefill**，且叠加了 [zigzag-cp](../../../concepts/parallelism/zigzag_cp.md)（CP 仅在 prefill 生效，与长上下文 `input_max_len` 16384/32768 搭配）时：**不能**让 prolog 算子按 `slot_mapping` 直写最终 paged cache，必须改成两段式 KV 写。覆盖 `kv_cache_quant_mode ∈ {int8(C8), 非量化}`，证据来自 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md)。这是把 [long-seq-prefill-context-parallel](long_seq_prefill_context_parallel.md) 落到 MLA-prolog 上时的一处必配正确性细节。

## 根因

zigzag-CP 把整条序列按 zigzag 规则切到各卡，单卡本地只算出**自己那片 shard 的 KV**。而 paged cache 的 `slot_mapping` 编址的是**全序列位置**——本地 shard KV 与全局 slot 对不上。若直写，KV 会落到错误的全局槽位。因此必须：本地先算 KV → CP all-gather 还原成全序 → 再按全局位置写回真 paged cache。

## 做什么：按是否开 CP 分两个调用分支

**CP prefill 分支（两段式）**：
- prolog 用 `cache_mode="BSND"`、`hidden_states.view(bsnd_bsz, bsnd_seq_len, -1)`、rope_sin/cos 同为 3D view，**不传 `cache_index`**；把本卡 KV 写进形状 `(batch, seq//cp_size, 1, D)` 的**临时 BSND cache**（恰为 `B*S` 大小、无 block padding）。
- 随后 `dist.all_gather_into_tensor` 收齐各卡分片，用 `reverse_split_list` / `cp_reverse_index` 还原 zigzag 序，再 `scatter_update_(…, axis=1)` 写回真的 nope / rope paged cache。

**非 CP prefill 分支（直写）**：
- prolog 用 `cache_mode="PA_BSND"`、`hidden_states.view(bsz*q_len, -1)`、传 `cache_index=slot_mapping.view(-1)`、rope_sin/cos `squeeze(1).squeeze(1)`；prolog 直写 paged cache，无需临时 cache / all-gather。

## Correctness / 风险 / rollback

- 正确性锚点：CP 下写回真 cache 必须发生在 all-gather + zigzag 逆序**之后**，用连续的 `scatter_update_`（axis=1）而非按全局 `slot_mapping` 的 scatter-nd 直写。
- 迁移边界：证据仅覆盖本仓 DeepSeek-V3.2-Exp 建模文件的 `npu_mla_prolog_v3`，适用面 = 同结构（MLA-prolog + paged KV + zigzag-CP prefill）的部署，不外推整栈。
- decode 无 CP，走非 CP/直写路径即可。
- rollback：关 CP（`cp_size=1`）即回落非 CP 直写分支，无临时 cache。

## 相关经验
- [因果稀疏注意力 CP prefill 的 zigzag 负载均衡：每 rank 两段两次调用](causal_cp_prefill_zigzag_actual_seqlens.md)

- 另见 [paged KV cache 按阶段选散点写算子：Prefill 连续段用 scatter_update_、Decode 单 token 用 scatter_nd](paged_kv_cache_write_scatter_update_vs_scatter_nd.md)。
- 另见 [MLA 前处理超级融合算子可用于长序列 Prefill — 勿被算子文档 Seq-Length 0~16 标注误导](mla_prolog_v3_prefill_seqlen_doc.md)。
- 另见 [量化特性所需状态被误挂在无关并行分支（CP 度）里 → 跳过该分支的配置静默丢状态（SFA C8 prefill 单卡漏填 per-token scale）](../../../runbooks/precision/quant_state_misattached_to_cp_branch.md)。
- 另见 [MLA / MLA-Prolog + Paged KV cache 部署的精度对齐要点](../../../runbooks/precision/precision_mla_prolog_paged_kv_cache.md)。
- 另见 [torch.split / 切片产出的非连续张量做展平：用 .reshape 而非 .view（bsz>1 才暴露，单批自测会掩盖）](../../../runbooks/runtime/torch_split_noncontiguous_view_reshape_minibatch.md)。


## Evidence

- **代码事实**（clone `@ea8d712a02e2`）：`models/deepseek-v3.2-exp/models/modeling_deepseek.py` 的 `DeepseekIndexerAttention.mlaprolog_prefill` / `DeepseekV3ForCausalLM.prepare_prefill_extra_input`：`cache_mode` 按 `cp_size` 在 `BSND`（不传 cache_index）/ `PA_BSND`（传 slot_mapping）分岔；BSND 临时 cache 形状 `(batch, seq//cp, 1, D)`；CP 分支 all-gather 后 `scatter_update_(axis=1)` 写回。
- **仓自报**：改动自报为 `fix` 类，但未记具体症状/根因，本页只述「CP 下为何要两段式 KV 写 + 两分支调用约定」，不断言修了何 bug；无 benchmark。
- 溯源下探：[cann-recipes-infer-pr-197-fix-tmp-kv-cache-set-to-bsnd-scatter-nd-update-replace-to-scatter-update](https://gitcode.com/cann/cann-recipes-infer/merge_requests/197)