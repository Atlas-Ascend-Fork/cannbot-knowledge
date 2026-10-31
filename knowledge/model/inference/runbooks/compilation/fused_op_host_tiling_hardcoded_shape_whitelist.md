---
type: Runbook
title: 昇腾融合算子 host-tiling 的硬编码 shape 白名单 / 必填输入契约拦截新结构模型 bringup
description: 昇腾融合算子 host-tiling 的硬编码 shape 白名单 / 必填输入契约拦截新结构模型 bringup。把一个结构参数（head-num / query 压缩维 / 专家数 / head-dim）与已支持模型不同的新模型接到昇腾现成融合算子上时，若算子在 host 侧 tiling 校验阶段直接报错、或某维度被拒，先怀疑算子把某个 shape 硬编码进了白名单/断言，而不是你的建模文件写错。这类拦截的正确处置是改算子侧放开白名单 / 补泛化，而非改模型 config 迁就算子。
tags:
- task.debugging
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/118
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/127
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/71
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/359
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/167
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:29:20Z'
platforms:
- agnostic
---

# 昇腾融合算子 host-tiling 的硬编码 shape 白名单 / 必填输入契约拦截新结构模型 bringup

## 适用场景

把一个**结构参数（head-num / query 压缩维 / 专家数 / head-dim）与已支持模型不同**的新模型接到昇腾现成融合算子上时，若算子在 host 侧 tiling 校验阶段直接报错、或某维度被拒，先怀疑**算子把某个 shape 硬编码进了白名单/断言**，而不是你的建模文件写错。这类拦截的正确处置是**改算子侧放开白名单 / 补泛化，而非改模型 config 迁就算子**。

## 问题信号（对号入座）

- **MLA prolog**：`mla_prolog`（MLA_PROLOG_V3）host tiling 硬编码只接受 Hcq（压缩 query 维 / `q_lora_rank`）=1536（DeepSeek 系值）；Hcq 不同的 MLA 模型（如 GLM-5 = 2048）被拦下报 `Hcq allows only 1536, got 2048`。
- **Lightning Indexer**：`lightning_indexer` 算子专化到 indexer query head-num（N1）=64，不支持其它 head-num；N1≠64 的 DSA 类模型无法直接复用。
- **MoE 门控**：CANN 的 `aclnnMoeGatingTopK`（`torch_npu.npu_moe_gating_top_k`）在旧版本把路由专家数上限写死 256，超 256 专家的 MoE（如 Kimi-K2-Thinking 的 384 专家）在 tiling 阶段直接失败。
- **线性注意力 CP 核**：ZECO CP GatedDeltaNet 核硬编码 head_dim K=128（`assert K==128`，BK=BV=128），`chunk_gated_delta_rule_npu` 一旦传入 `cp_group` 就走 ZECO 路径，K≠128 直接命中 assert 崩溃、无回退。
- **必填输入契约**：`lightning_indexer` 在 key layout=PA_BSND 时，tiling 解析会强校验 `block_table` 与 `actual_seq_lengths_key` 非空、且 `block_table` dtype=int32，任一不满足即 `GRAPH_FAILED` 并打 `OPS_LOG_E`。

## 根因

昇腾融合算子把 host tiling 做成「按已知模型的固定 shape 特化」以简化 kernel 分支——特化点表现为**硬编码常量白名单 / assert / 必填输入约束**。它们不是技术本身的限制，而是**该参考实现只覆盖了标定过的那组 shape**。新结构模型的维度落在白名单外时被 host 校验挡下，报错常在 tiling/prepare 阶段而非 kernel 计算阶段。

## 修法 / 手段

- **在算子侧放开约束**：把硬编码常量改成从入参/config 读取并做泛化适配（如 mla_prolog 放开 Hcq 白名单、lightning_indexer 放开 N1 head-num 拦截并适配 N1 泛化点），而不是改建模文件去凑那个常量。
- **专家数超上限**：升级到已放开专家上限的 CANN 版本，或换用支持大专家数的门控算子路径。
- **CP 核 head_dim**：给非 128 head_dim 的混合注意力模型上 CP 前，**先确认核的 head_dim 约束**（ZECO=128）；不满足则不要传 `cp_group`（回落非 CP 路径）或改核适配。
- **必填输入契约**：走 PA_BSND 的 LI 调用必须备齐 `block_table`（int32）与 `actual_seq_lengths_key`。

## 风险 / 边界

- 放开白名单后须重新验证精度/性能（特化常量往往对应过 tiling 调优）。
- 上面各常量是各自参考实现在其钉定版本的值，可能随版本演进；迁移前以目标 commit 的算子源为准。

## 相关经验

- ZECO CP GDN 的完整机制与约束见 [qwen3-next-gdn-context-parallel-zeco](../../optimizations/cases/qwen3_next_gdn_context_parallel_zeco.md)。
- FIA 的 `actual_seq_lengths_kv` 类型随后端不同（另一类算子输入契约）见 [fia-actual-seq-lengths-kv-backend-type](../runtime/fia_actual_seq_lengths_kv_backend_type.md)。
- 融合算子按硬件条件门控回退见 [fused-op-hardware-conditional-fallback](../../optimizations/rules/fused_op_hardware_conditional_fallback.md)。
- 另见 [AscendC 算子 host 侧未覆盖运行时可达配置空间：缺省可选输入被无条件读取、模板参数取值未全枚举 → 特定 config 崩溃 / npu fail / 无 tiling key](ascendc_op_host_optional_input_and_tiling_key_coverage.md)。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/118)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/127)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/71)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/359)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/167)（evidence）
