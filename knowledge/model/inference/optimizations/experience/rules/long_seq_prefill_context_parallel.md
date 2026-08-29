---
type: Optimization
title: 长序列 Prefill 注意力优先 Context Parallel（CP 仅 prefill 生效，MoE 复用 CP 域走 EP）
description: 长序列 Prefill（本经验覆盖 16K–166K，示例常以 64K 计），注意力单 rank 要承担整条序列的计算量与 activation 内存，OOM 风险高、TTFT 难控。此时注意力优先选 context-parallel（CP），把序列维切到多 rank 均摊，单 rank 计算量与 activation 内存都变小、TTFT 可控。约束 cp_size == world_size（DeepSeek-V3.2-Exp / Kimi-K2-Thinking 实践都令 CP 铺满整个 world）。
tags:
- task.optimization
- topic.attention
- topic.mixture_of_experts
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/27
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/3
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/93
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/235
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/114
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# 长序列 Prefill 注意力优先 Context Parallel（CP 仅 prefill 生效，MoE 复用 CP 域走 EP）

## 条件 → 优先尝试 CP

长序列 Prefill（本经验覆盖 16K–166K，示例常以 64K 计），注意力单 rank 要承担整条序列的计算量与 activation 内存，OOM 风险高、TTFT 难控。此时注意力**优先选 [context-parallel](../../../concepts/parallelism/context_parallel.md)（CP）**，把序列维切到多 rank 均摊，单 rank 计算量与 activation 内存都变小、TTFT 可控。约束 `cp_size == world_size`（DeepSeek-V3.2-Exp / Kimi-K2-Thinking 实践都令 CP 铺满整个 world）。

这条规则在 MoE + 稀疏/稠密注意力的长序列 Prefill 上反复成立：[deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md)（DSA 稀疏注意力）、[kimi-k2-thinking](../../../concepts/models/kimi_k2_thinking.md)（MoE 稠密注意力）、[qwen3-next](../../../concepts/models/qwen3_next.md)（混合注意力）。

## 为何 CP 而非 TP / DP

- **不用 Attention-DP**：DP 让每个 rank 各推一条完整超长序列，总计算量大、TTFT 高。
- **不用 TP（尤其 DSA/稀疏 indexer）**：TP 本是压 TTFT 的常规手段，但对含 [lightning-indexer](../../../concepts/kernels/lightning_indexer.md) 的 DSA，Indexer 计算量与 $S^2$ 成正比、是长序列主要瓶颈，且该模块**对 head 轴做 Reduce Sum**——TP 沿 head 切会引入大量通信开销拖累整网。稠密注意力下超长序列的 TP 组内 All-Reduce 开销同样巨大，且 head 数会限制 TP 上限（如 Qwen3-Next 注意力 head 数 16 → 纯 TP 最多 16TP，且切 head 也不解决序列维 OOM）。

维护者对「DS v3.2 的 SFA 是否支持 CP」明确答复：支持，推理 prefill 用的就是 CP 并行。

## CP 负载均衡：ZigZag 对称切片 + Token 重排

因果注意力下，CP 若简单按 rank 顺序切片会负载不均（靠前 rank 关注历史 KV 少、算得少；靠后 rank 算得多）。做法：把序列按 **`cp_size*2`** 切成对称 block，每 rank 负责**头尾对称的两个切片**；进 [lightning-indexer](../../../concepts/kernels/lightning_indexer.md) / [sparse-flash-attention](../../../concepts/kernels/sparse_flash_attention.md)（或 Gated Attention）计算前用 **Token 重排**把 KV 还原回因果顺序。DeepSeek-V3.2-Exp 在 `input_ids` 上按 `cp_size*2` 切片实现；Qwen3-Next 在 SGLang 侧以 `linear_to_zigzag_all_to_all` / `zigzag_to_linear_all_to_all`（`prepare_attn` 时 All-to-All 转 ZigZag 排布、`prepare_mlp` 时转回因果序）实现，由 `CP_USE_ZIGZAG=1` 开启，面向长序列单 batch 场景。

CP 计算流水（64K、cp_size 为例）：每 rank 拿 `S/cp_size` 个 q token（DeepSeek-V3.2-Exp 64 卡即 1K/rank），算完本地 KV 后对全 CP 域 KV 做 **AllGather** 得完整 KV，再用本地 q + 完整 KV 做注意力。

## MoE 复用 CP 通信域走 EP，其它模块切分

- **MoE**：沿用 [expert-parallel](../../../concepts/parallelism/expert_parallel.md)（EP），且 **EP 复用 CP 通信域**，不额外建组。
- **O_proj**：内存占用大，走局部 TP 切分，前后引入 AllToAll 与 ReduceScatter（DeepSeek-V3.2-Exp `oproj_tp_size=8`）。
- **Embedding / LM Head**：[tensor-parallel](../../../concepts/parallelism/tensor_parallel.md)（tp_size 控在单 Node 内）；LM Head 需在整个 CP 域内 AllGather + Token 重排把 feature map 还原到原序列排布。

## CP 仅 Prefill 生效（is_prefill 门控，易踩坑）

CP 全程受 `is_prefill` 门控：建模里 `cp_size = self.cp_size if is_prefill else 1`，所有 all-gather/切分分支均写作 `if self.cp_size > 1 and is_prefill`；YAML 也标 `cp_size ... only active at prefill stage`。**即使 Decode 的 yaml 写了 `cp_size: 128`，Decode 阶段 CP 也不生效**，注意力回退 DP。读配置时不要据 Decode yaml 的 `cp_size` 推断 Decode 有 CP。长序列 memory-bound decode 的 KV 切分是另一条路（[kvp](../../../concepts/parallelism/kvp.md)，见 [kvp-longseq-decode](../../../guides/experience/interventions/kvp_longseq_decode.md)）。

## 混合注意力模型的分层异构策略（Qwen3-Next）

混合注意力模型按层类型分派并行：

- **Gated Attention 层（≈O(S²)）→ CP + TP 混合**：CP 切序列降 activation 内存、TP 切 head；CP 复用 SGLang 的 DP 通信域（`dp_size = max(dp_size, cp_size)`，CP 与 DP 不可同开）。示例 m=4 CP × n=2 TP、64K 输入：每 CP rank 处理 16K token，rank 内 qkv_proj 按 TP2 算，算完 KV 对全 CP 域 AllGather 得完整 KV，注意力后在 TP 组内 Reduce-Scatter 得 MoE 输入排布。
- **GDN（GatedDeltaNet）层 → 纯 TP**：GDN 含沿 Sequence 的卷积、不宜切序列，且 num_head 足够 TP 切分。要让 GDN 也吃到 CP 加速需 ZECO 技术，见 [qwen3-next-gdn-context-parallel-zeco](../../../guides/experience/interventions/qwen3_next_gdn_context_parallel_zeco.md)。

## 部署规模：超长序列须多机大 EP（参考实现约束）

CP 压 TTFT 只解决「单 rank 长序列计算/显存」这一半；另一半是「序列越长、整体内存/算力需求越大」的部署规模。参考实现里最小部署单元为**单机**、仅能吃约 **4K** 序列；**256K 超长序列须多机大 EP 协同部署**（Attention 走 CP 均摊、MoE 走 EP，复用同一通信域）。PD 分离下 Prefill 用 M 个节点、Decode 用 N 个节点，**M/N 按资源与 SLA 在 1~24 内弹性调整**（非固定配比）。规划超长序列部署时先据此估节点数——别指望单机撑起 256K；这是该参考实现的规模边界，非 CP 技术本身限制。维护者确认 Kimi-K2-Thinking 面向长序列、已适配 CP 并行、可支持 256K 超长序列推理（CANN 0day 部署）。

## 反例 / 边界

- 适用面 = MoE / DSA / 混合注意力的**长序列 Prefill**；不外推为昇腾栈通用并行律。
- CP 常带 PD-分离约束：Qwen3-Next 要求 `cp_size < tp_size`、CP 仅 PD 分离场景开、PD 卡数需相同（SGLang KV 传输限制）、CP 不与 DP 同开。
- 无端到端 CP vs TP/DP 的独立复测 TTFT 数字，收益为机制层结论；不写量化收益。
- CP 下 MLA-prolog 的 paged KV cache 写法有额外正确性要求，见 [mla-prolog-zigzag-cp-kv-write](mla_prolog_zigzag_cp_kv_write.md)。

## 相关经验
- [因果稀疏注意力 CP prefill 的 zigzag 负载均衡：每 rank 两段两次调用](causal_cp_prefill_zigzag_actual_seqlens.md)

## Evidence

- **代码事实**（clone `@fa6892b`）：DeepSeek-V3.2-Exp `deepseek_v3.2_exp_inference_guide.md#并行策略` + `model_infer.py`（`is_prefill and cp_size>1` 才切 s）+ prefill yaml `cp_size=64==world_size, only active at prefill`。
- **代码事实**（clone `@da13d66`）：Kimi-K2-Thinking `modeling_deepseek.py` 的 `cp_size = self.cp_size if is_prefill else 1` 门控。
- **代码事实**（clone `@874b41d`）：Qwen3-Next stage4 CP patch 新增 `zigzag_cp_utils.py`（`linear_to_zigzag_all_to_all` / `cp_all_gather_rearrange_output`）、`dp_size=max(dp_size,cp_size)`、`优化文档#并行策略`。
- **维护者确认**：DS v3.2 的 SFA「支持，推理 prefill 使用的就是 cp 并行」；Kimi-K2-Thinking「主要面向长序列场景，针对该场景适配了 CP 并行，可支持 256K 超长序列推理」。
- **doc 披露**（clone `@2c45117`）：Kimi-K2-Thinking `kimi_k2_thinking_inference_guide.md` 的「并行策略 / Prefill 并行策略」+ `config/kimi_k2_thinking_rank_64_64ep_prefill_benchmark.yaml` + `figures/k2_prefill_cp.jpg`——Prefill Attention 用 CP、MoE 用 EP、单机 4K / 256K 多机大 EP，均对上。
- 溯源下探：
  - [cann-recipes-infer-pr-3-feat-add-deepseek-v3-2-exp-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/3)
  - [cann-recipes-infer-pr-93-feat-support-kimi-k2-thinking](https://gitcode.com/cann/cann-recipes-infer/merge_requests/93)
  - [cann-recipes-infer-pr-235-feat-support-qwen-next](https://gitcode.com/cann/cann-recipes-infer/merge_requests/235)
  - [cann-recipes-infer-issue-27-question-ds-v3-2-sfa-cp-sp-mindie](https://gitcode.com/cann/cann-recipes-infer/issues/27)
  - [cann-recipes-infer-issue-114-question-kimi](https://gitcode.com/cann/cann-recipes-infer/issues/114)

<!-- cannbot:related:start -->
## 相关

- [Context Parallel](../../../concepts/parallelism/context_parallel.md)（`related`）：“长序列 Prefill（本经验覆盖 16K–166K，示例常以 64K 计），注意力单 rank 要承担整条序列的计算量与 activation 内存，OOM 风险高、TTFT 难控。此时注意力**优先选 ［context-parallel］(../../../concepts/parallelism/context_parallel.md)（CP）**，把序列维切到多 rank 均摊，单 rank 计算量与 activation 内存都变小、TTFT 可控。”；“- Attention 计算前通过 AllGather 收集完整的 KV”。概念卡给出规则所采用的 Sequence 切分、完整 KV 收集和本地 Q 计算合同。
- [MLA-prolog + zigzag-CP Prefill 必须用两段式 KV cache 写（勿按 slot_mapping 直写 paged cache）](mla_prolog_zigzag_cp_kv_write.md)（`related`）：“CP 下 MLA-prolog 的 paged KV cache 写法有额外正确性要求，见 ［mla-prolog-zigzag-cp-kv-write］(mla_prolog_zigzag_cp_kv_write.md)。”；“而 paged cache 的 `slot_mapping` 编址的是**全序列位置**——本地 shard KV 与全局 slot 对不上。若直写，KV 会落到错误的全局槽位。因此必须：本地先算 KV → CP all-gather 还原成全序 → 再按全局位置写回真 paged cache。”。目标规则补齐长序列 CP 在 MLA-prolog 写 cache 时的必配生产消费顺序。
- [SFA/DSA 稀疏注意力叠加 Context Parallel：跨 CP 组重建完整 KV 的 all_gather 路径](../../../guides/experience/interventions/sfa_dsa_cp_cross_group_kv_allgather.md)（`related`）：“CP 计算流水（64K、cp_size 为例）：每 rank 拿 `S/cp_size` 个 q token（DeepSeek-V3.2-Exp 64 卡即 1K/rank），算完本地 KV 后对全 CP 域 KV 做 **AllGather** 得完整 KV，再用本地 q + 完整 KV 做注意力。”；“本页给出该场景下的一个可执行做法：**在注意力/indexer 计算前，先 `index_select` 出有效 block、再依次做 DCP all_gather 和 PCP all_gather 重建完整 KV**，并配套一条**硬前置**——`kv_cache_interleave_size` 必须等于 `block_size`。”。目标指南把焦点的全域 KV AllGather 落到 paged SFA/DSA 的顺序、索引和硬前置。
- [ZECO — 让线性注意力 / GDN 吃到序列并行（Context Parallel），打破 chunk 递推的跨 rank 顺序依赖](../../../guides/experience/interventions/qwen3_next_gdn_context_parallel_zeco.md)（`related`）：ZECO 卡说明“于是线性注意力层也能沿序列维切到多 rank（CP），与全注意力层的 CP（ZigZag 负载均衡，见 ［long-seq-prefill-context-parallel］(../../../optimizations/experience/rules/long_seq_prefill_context_parallel.md)）配齐。”；选型卡限定“CP 全程受 `is_prefill` 门控”，因此前者扩展的是长序列 Prefill 的线性注意力覆盖面，而不是 Decode 并行。
- [torch.split / 切片产出的非连续张量做展平：用 .reshape 而非 .view（bsz>1 才暴露，单批自测会掩盖）](../../../runbooks/runtime/torch_split_noncontiguous_view_reshape_minibatch.md)（`related`）：“因果注意力下，CP 若简单按 rank 顺序切片会负载不均（靠前 rank 关注历史 KV 少、算得少；靠后 rank 算得多）。做法：把序列按 **`cp_size*2`** 切成对称 block，每 rank 负责**头尾对称的两个切片**；进 ［lightning-indexer］(../../../concepts/kernels/lightning_indexer.md) / ［sparse-flash-attention］(../../../concepts/kernels/sparse_flash_attention.md)（或 Gated Attention）计算前用 **Token 重排**把 KV 还原回因果顺序。”；“参考实现在 cann-recipes-infer DeepSeek-V3.2-Exp（［DSA］(../../concepts/modules/dsa.md)）的 ［lightning indexer］(../../concepts/kernels/lightning_indexer.md) `Indexer.forward` 的 context-parallel prefill 分支（`cp_size > 1 and is_prefill`）：该分支 all-gather 后按 `cp_reverse_index` 重排、沿 `dim=1` split 成 prev/next（load-balanced / ［zigzag-CP］(../../concepts/parallelism/zigzag_cp.md) 双 chunk 重构），涉及 C8 KV cache 路径的 `query_dequant_scale_prev/next` 与通用路径的 `weights_prev/next` 共 4 处 `.view`→`.reshape`。”。目标 runbook 给出焦点双切片重排在 minibatch 下的非连续内存故障与修法。
- [因果稀疏注意力 CP prefill 的 zigzag 负载均衡：每 rank 两段两次调用 + 头尾因果前缀 actual_seq_lengths（qlen≠kvlen）](causal_cp_prefill_zigzag_actual_seqlens.md)（`related`）：每次调用的 `actual_seq_lengths_key` 精确等于该段 token 的因果前缀长，配合完整 K，语义等价于单卡因果计算。；因果注意力下，CP 若简单按 rank 顺序切片会负载不均（靠前 rank 关注历史 KV 少、算得少；靠后 rank 算得多）。做法：把序列按 **`cp_size*2`** 切成对称 block，每 rank 负责**头尾对称的两个切片**；进 ［lightning-indexer］(../../../concepts/kernels/lightning_indexer.md) / ［sparse-flash-attention］(../../../concepts/kernels/sparse_flash_attention.md)（或 Gated Attention）计算前用 **Token 重排**把 KV 还原回因果顺序。；长序列规则确定对称切片与 Token 重排，actual-seqlens 规则给出每段因果前缀实参，把部署决策落到算子调用。
- [跨 Prefill/Decode 默认 config 集群规模不一致 + 非默认卡数验证边界](prefill_decode_cluster_scale_mismatch.md)（`related`）：- **迁移时按阶段独立对齐卡数**：`world_size` 设为 `2 × 目标卡数`、`cp_size`（［CP］(../../../concepts/parallelism/context_parallel.md)）随 `world_size` 对齐；prefill 与 decode 分别核对，不假设同规模。；长序列 Prefill（本经验覆盖 16K–166K，示例常以 64K 计），注意力单 rank 要承担整条序列的计算量与 activation 内存，OOM 风险高、TTFT 难控。此时注意力**优先选 ［context-parallel］(../../../concepts/parallelism/context_parallel.md)（CP）**，把序列维切到多 rank 均摊，单 rank 计算量与 activation 内存都变小、TTFT 可控。约束 `cp_size == world_size`（DeepSeek-V3.2-Exp / Kimi-K2-Thinking 实践都令 CP 铺满整个 world）。。规模迁移规则要求 prefill 独立对齐 CP，长序列规则解释该约束用于分摊序列计算和激活内存。
<!-- cannbot:related:end -->
