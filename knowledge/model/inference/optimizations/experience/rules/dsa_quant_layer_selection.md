---
type: Optimization
title: 稀疏注意力 / 共享 prolog 结构的量化选层：按瓶颈分级 + 共享融合算子输入保持 BF16
description: 稀疏注意力 / 共享 prolog 结构的量化选层：按瓶颈分级 + 共享融合算子输入保持 BF16。给一个稀疏注意力 / 双 prolog（如 dsa：lightning-indexer + sparse-flash-attention + mla）结构做 w8a8c8（含 C8 KVCache）量化时，会本能地「能压 int8 就压」。这里两条选层原则决定量化谁、量到哪一级，照着走通常只有极少数 Linear 真正走 W8A8——那不是保守，而是结构约束下的正确取舍。
tags:
- task.optimization
- topic.attention
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/7
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/8
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 稀疏注意力 / 共享 prolog 结构的量化选层：按瓶颈分级 + 共享融合算子输入保持 BF16

## 适用场景

给一个稀疏注意力 / 双 prolog（如 [dsa](../../../concepts/modules/dsa.md)：[lightning-indexer](../../../concepts/kernels/lightning_indexer.md) + [sparse-flash-attention](../../../concepts/kernels/sparse_flash_attention.md) + [mla](../../../concepts/modules/mla.md)）结构做 [w8a8c8](../../../concepts/quantization/w8a8c8.md)（含 C8 KVCache）量化时，会本能地「能压 int8 就压」。这里两条选层原则决定**量化谁、量到哪一级**，照着走通常只有极少数 Linear 真正走 W8A8——那不是保守，而是结构约束下的正确取舍。

## 原则一 · 按瓶颈性质分级（compute-bound → 算 int8；memory-bound → 只量存储）

先分清某算子是算力瓶颈还是访存瓶颈，再决定量化位是「省算力（真的用 int8 计算）」还是「省显存（只量存储、反量化后仍 16 位算）」：

- **计算受益点 → 推到 int8 计算**：[lightning-indexer](../../../concepts/kernels/lightning_indexer.md) 的 BatchMatmul 是算力受益点，量到 A8C8 走 int8 计算，直接降单算子时延。
- **访存受益点 → 只量存储、算仍 16 位**：MLA / SFA 的 KVCache 是访存受益点，做 C8「存 8 算 16」拿约 2 倍内存收益打高吞吐，不推到 int8 计算。

> **不要做：为 SFA 追求「存 8 算 8」。** SparseFlashAttention 的耗时瓶颈在稀疏 topk 后按索引 gather KV 的**离散聚合访存**，不在计算密度；即使把 KVCache 计算侧也降到 int8，端到端时延依旧无法提升，只徒增一条 int8 计算路径的工程投入。落地上 KVCache dtype 设 int8、另并列一份 fp16 per-token-head scale cache 供反量化，注意力计算侧保持 BF16。这条可迁移到其它 gather-bound 的稀疏 attention。

## 原则二 · 共享融合算子输入的 Linear 保持同 dtype 不量化

当一份 Linear 输出（BF16）被**多个融合算子共享作输入**时，其量化决策必须对齐所有下游算子——只要有一个下游要求 fp16 输入，这份共享输入就整体保持 BF16 不量化。

- 触发结构：[indexer-prolog](../../../concepts/kernels/indexer_prolog.md) 与 [mla-prolog](../../../concepts/kernels/mla_prolog.md) 吃同一份前置 BF16 输入。IndexerProlog 被设计成 `weights_proj` 出 fp16 且其输入不量化，这份输入又与 MLAProlog 共享。
- 若把该共享输入关联的 Linear 也量化，就得为两个融合算子各存一份不同精度的输入副本（或多做一次量化 / 反量化），得不偿失。
- 因此把 MLA 输入侧关联的 Linear（`q_a_proj` / `kv_a_proj_with_mqa` 等）统一不量化，同一份 BF16 数据同时喂 IndexerProlog 与 MLAProlog，省一份量化输入拷贝。
- 可迁移条件：模型里有两个并行分支共享同一输入（DSA 系双 prolog、或其它双头结构）时，让共享输入的 Linear 保持同一 dtype。

## 落到本仓布局的结果

两原则叠加后，实际只有计算主体的少数 Linear 走 W8A8——MLA 量化下游独占的 `q_b_proj`、MLAEpilog 的 `o_proj`，Indexer 量化 `wq_b`，加 MoE 路由 / 共享专家；共享 / 前置的 `q_a_proj` / `kv_a_proj_with_mqa` / `kv_b_proj` / `indexer.wk` / `indexer.weights_proj` 及 `lm_head` 进不量化清单，KVCache / Indexer Cache 走 C8。逐层量化布局的完整快照属静态模型页维护，此处只承接「该量化哪层、为什么」的判断。

量化粒度（供选型对齐）：W8 = 权重静态 Per-Channel int8；A8 = 数据动态 Per-Token int8；Lightning Indexer A8C8 = Per-Token-Head int8；KVCache C8 = Per-Token-Head-Tile-128 int8。

## 参考实现及其约束

参考实现在 cann-recipes-infer 的 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md) W8A8C8（`convert_model.py` 的 `generate_ignore_item` 不量化清单 + `DeepseekIndexerAttention` / `indexer.py` 的 `quant_config` 门控）。适用面限定到 DSA（Indexer + MLA 双 prolog）结构，不升为整个昇腾栈通用律。

- MoE 专家的进一步降位（路由专家 W4A8 等）见 [moe-role-based-precision-allocation](moe_role_based_precision_allocation.md)。
- C8 int8 KV 在 MLA/SFA/MLA-prolog 上的具体算子接线见 [mla-c8-int8-kv-cache-op-wiring](mla_c8_int8_kv_cache_op_wiring.md)。
- 用 PyPTO 把该前段做成低 bit 量化融合算子的 Hadamard 消 outlier / MTE-bound 手段见 [pypto-dsa-fused-attention-decompose-quant](pypto_dsa_fused_attention_decompose_quant.md)。

## 相关经验

- 另见 [sglang 单卡 tp1 拉起 OOM：关 ACL/NZ 权重格式转换（SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT=1）](../../../runbooks/performance/sglang_tp1_oom_disable_nz_weight.md)。
- 另见 [AscendC 融合算子 Tiling 定块与片上 Buffer 预算：核间 m 轴取舍 + L1/L0 字节账 + UB double-buffer 全计入](../cases/ascendc_attention_op_tiling_budget.md)。


## Evidence

- `doc 披露` + `diff 事实`（@9d9199e3577c）：量化策略 doc 明写两条设计理由（按瓶颈分级、共享输入不量化省拷贝）；建模 diff 把 `q_a_proj` / `kv_a_proj_with_mqa` 置 `quant_config=None`、`indexer.wq_b` 置 `config.quant_config`。
- `diff 事实`（@2c45117）：`convert_model.py generate_ignore_item` 不量化清单、`init_cache_for_indexer` 在 C8 时 KVCache dtype = int8 + 并列 fp16 `past_key_scales`。
- `doc 披露`（@9d9199e3577c）：「SparseFlashAttention 耗时瓶颈点在离散聚合访存，即使实现存 8 算 8，端到端时延依旧无法提升」为维护者设计理由，非独立 profiling 复测。
- 溯源下探：
  - [cann-recipes-infer-pr-7-feat-add-deepseek-v3-2-exp-w8a8c8-quantization-support](https://gitcode.com/cann/cann-recipes-infer/merge_requests/7)
  - [cann-recipes-infer-issue-8-rfc-deepseek-v3-2-exp-w8a8c8](https://gitcode.com/cann/cann-recipes-infer/issues/8)