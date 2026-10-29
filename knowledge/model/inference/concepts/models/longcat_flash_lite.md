---
type: Concept
title: LongCat-Flash-Lite
description: LongCat-Lite 的双子层 MLA、shortcut MoE、零专家和 N-gram Embedding 结构及文档差异。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_ep.md
  role: primary
created_at: '2026-04-16T00:00:00Z'
updated_at: '2026-10-21T10:02:02Z'
platforms:
- a2
- a3
---



# LongCat-Flash-Lite

## Summary

LongCat-Flash-Lite 为包含MLA、shortcut MoE与N-gram Embedding的减配验证模型。14层双子层结构包含路由与identity experts；大N-gram表与主Embedding是不同对象，词表、FFN维度应分开解释。

平台配置、开关和验收步骤见[模型部署流程](../../guides/models/longcat_flash_lite_deployment.md)，此处只保留模型机制。

## Architecture And Serving Traits

减配结构（终态报告 §1.1；层/expert 数取 `LongcatFlashNgramConfig` 默认值）：

- **14 个 decoder layer**（`LongcatFlashNgramConfig` 默认 `num_layers=14`；满配 `LongcatFlashConfig` 默认 61 层）；每层 `LongcatFlashDecoderLayer` 为 **dual sub-layer + shortcut MoE** 结构：2 个 `LongcatFlashMLA` attention block + 2 个 `LongcatFlashMLP`（Dense）+ 1 个共享 `LongcatFlashMoE`（其输出作为 shortcut 加到 sub-layer 1）。
- **MLA**（`LongcatFlashMLA`）：`q_lora_rank=1536`、`kv_lora_rank=512`、`qk_nope_head_dim=128`、`qk_rope_head_dim=64`、`v_head_dim=128`、32 heads。
- **MoE**（`LongcatFlashMoE`）：**256 routed expert + 128 zero/identity expert**（`zero_expert_num`，identity 副本每卡持有、不参与 EP 切分，计算 `MoE(x)=x`）、top-12 路由（`LongcatFlashTopkRouter`）。
- **两个独立 FFN 中间维**（`LongcatFlashNgramConfig` 子类同时携带，非字段歧义）：MoE expert FFN 中间维 `expert_ffn_hidden_size=1024`（EP 报告 §1.1 记 `expert_intermediate=1024`），Dense MLP 中间维 `ffn_hidden_size=6144`（TP 报告 §1.1 文字记 Dense MLP `3072→6144→3072`）——分属 MoE expert 与 Dense MLP 两个子模块，互不冲突。
- **N-gram Embedding**（`NgramEmbedding`）：12 个 sub-embedder 子表 + `post_proj`，是显存大头（~31 B），必须 TP 切分；`ngram_context` 用 `register_buffer` 持久化以便整图编译。主 `embed_tokens` / `lm_head` 在钉定版代码中按基础 vocab `vocab_size=131072` 构造（`embed_tokens = VocabParallelEmbedding(self.vocab_size, ...)`、`lm_head = ColumnParallelLinear(output_size=config.vocab_size, ...)`，`self.vocab_size = config.vocab_size = 131072`，与 TP 报告 §1.1 一致）；EP 报告 §1.1 记 `VocabParallelEmbedding(155136 → 3072)` / `lm_head(3072 → 155136)` 的 `155136` 仅见于 EP 报告 L17/L23，代码与 config 均无此值，属未解释的 doc-vs-code 文档差异。注意 `ngram_vocab_size_ratio=78` 与 155136 无关：它对应 ngram 子表 vocab `self.m = ngram_vocab_size_ratio * vocab_size`（=78×131072≈10.2M，EP 报告另行单列为 `ngram_embedders[12] (~10.2M→256)`），既非主表 vocab、与 155136 亦无算术或结构关系。

## Gaps（报告 §9 未覆盖 + doc≠code）

平台与实现缺口分别见模型Guide、[EP来源草稿](../../optimizations/benchmark_observations/longcat_lite_ep_source_observations.md)。报告的RS+AG描述不能替代固定源码中缺失的实现；精度漂移不得直接解释为已验收语义等价。

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/longcat_flash_lite_deployment.md)：配置、开关、失效条件与回退入口。
- [LongCat-Lite A3 MLA-Prolog 与长输入的来源观测](../../optimizations/benchmark_observations/longcat_lite_a3_prolog_source_benchmark.md)：固定来源自报，未经本仓独立复测。
- [LongCat-Lite EP 报告的平台与源码待核验观测](../../optimizations/benchmark_observations/longcat_lite_ep_source_observations.md)：来源条件待核验，保持draft。
- [Ngram入图案例](../../optimizations/cases/longcat_lite_ngram_graph_host_gap.md)：既有TP8实现差异与图外/入图证据。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/longcat_flash_lite/agentic/optimization_report_ep.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_ep.md)（EP 部署：§1 结构 / §2 基线 / §3 并行切分 / §4.1 MLA 压缩缓存+PA / §4.2 MLA Prolog / §4.3 Prefill TP+SP（doc≠code，见 Gaps）/ §5 融合 / §6 图模式 / §7 吞吐扩展 / §8 演进 / §9 未覆盖）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/longcat_flash_lite/agentic/optimization_report_tp.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_tp.md)（TP 部署：§2.1 精度基线 / §4 MLA+PA / MLA Prolog（A3 decode）/ §5 融合 / §6 图模式 / §7.1 A2 vs A3 / §7.2 长输入 4K·1K / §8 演进）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/longcat_flash_lite/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/README.md)（A2/A3、CANN 9.0.0、Agent Skills 工作流）；[`models/longcat_flash_lite/config/`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/config)（`8ep` / `8ep_b8` / `8tp` / `8tp_4k1k` 四份部署 YAML）；[`models/longcat_flash_lite/models/modeling_longcat_flash_lite.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py)（`LongcatFlashMLA`/`LongcatFlashMoE`/`LongcatFlashDecoderLayer`/`NgramEmbedding`/`LongcatFlashNgramForCausalLM`、`enable_moe_mc2_dispatch` L1630、`copy_expert_num` L914/929、PA `cache_mode="PA_NZ"` L370/496）；[`models/longcat_flash_lite/models/configuration_longcat_flash_lite.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/models/configuration_longcat_flash_lite.py)（`LongcatFlashNgramConfig` `num_layers=14` / `n_routed_experts=256` / `q_lora_rank=1536` / `kv_lora_rank=512`）
- 原始模型：Meituan `meituan-longcat/LongCat-Flash-Lite`（HF）
- 引入提交：`feat: add longcat-flash-lite model optimized by agent skills`（39595c0，MR!348，refactor-longcatflashlite→master）

## Links

- [longcat-flash](longcat_flash.md)（满配模型；Lite 为其减配验证版）
- [mla](../modules/mla.md)
- [mla-prolog](../kernels/mla_prolog.md)
- [kv-cache-manager](../frameworks/kv_cache_manager.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)
- [double-routing](../techniques/double_routing.md)
- [npu-graph-mode](../techniques/npu_graph_mode.md)
- [atlas-a3](../platforms/atlas_a3.md)
