---
type: Concept
title: GLM-5
description: GLM-5 的 DSA、MLA/Indexer 与 MoE 规格；平台配置、投机解码与性能记录分别维护。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/README.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/config/glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml
  role: supporting
created_at: '2026-06-03T00:00:00Z'
updated_at: '2026-10-22T10:36:46Z'
platforms:
- a3
---




# GLM-5

## Summary

GLM-5 在本卡对应744B/激活40B的MoE检查点，采用MLA主干与Lightning Indexer组成的DSA。与DeepSeek-V3.2-Exp为机制同族，层数、维度、词表和实现参数不同，不能把“沿用方案”解释成所有配置及代码完全相同。

平台配置、开关和验收步骤见[模型部署流程](../../guides/models/glm_5_deployment.md)，此处只保留模型机制。

## 架构图（stock HF 基线）

下图为 GLM-5 的 stock HuggingFace 架构先验（部署无关），依据 `zai-org/GLM-5/config.json` 与 transformers `glm_moe_dsa` 建模代码。

```mermaid
flowchart TD
    in([input tokens])
    in --> embed["Embed : V → 6144"]

    subgraph block ["Block × 78"]
        direction TB
        n1[RMSNorm]
        attn["DSA Attn<br/><i>MLA Q/KV LoRA + sparse indexer</i>"]
        n2[RMSNorm]
        moe[MoE FFN]
        n1 --> attn
        attn -->|+ residual| n2
        n2 --> moe
    end

    embed --> n1
    moe -->|+ residual| fnorm[RMSNorm]
    fnorm --> head["LMHead : 6144 → V"]
    head --> logits([logits])
```
*来源：`zai-org/GLM-5/config.json`（verified 2026-05-15，`architectures=["GlmMoeDsaForCausalLM"]`、`model_type=glm_moe_dsa`）+ HuggingFace transformers main `src/transformers/models/glm_moe_dsa/{configuration_glm_moe_dsa.py, modeling_glm_moe_dsa.py}`（verified 2026-05-15）。*

精简参数表（与部署用 `configuration_glm.py` 默认值一致）：

| 参数 | 值 |
| --- | --- |
| vocab / hidden / n_layers | 154880 / 6144 / 78 |
| n_routed_experts / n_shared_experts / top_k | 256 / 1 / 8 |
| dense intermediate / moe intermediate | 12288 / 2048 |
| dense层 / MoE层（从1计数） | 1–3 / 4–78 |
| routed_scaling_factor / n_group / topk_group | 2.5 / 1 / 1 |
| scoring / balance | sigmoid / noaux_tc |
| max_position_embeddings / rms_norm_eps | 202752 / 1e-5 |
| norm_topk_prob / tie_word_embeddings | True / False |

> 层类型由 `GlmMoeDsaConfig` 硬编码 `mlp_layer_types = ["dense"]×3 + ["sparse"]×75`，不通过 `first_k_dense_replace` 配置。

## DSA 注意力（MLA + Indexer）

GLM-5 的注意力是 `GlmMoeDsaAttention`（`modeling_glm.py:661`），即 V3.2-Exp 同款 DSA（MLA + Lightning Indexer），算子机理见 [dsa](../modules/dsa.md)、[mla](../modules/mla.md)、[lightning-indexer](../modules/lightning_indexer.md)。

- **MLA 维度**：MHA（`num_attention_heads = num_key_value_heads = 64`）。`q_lora_rank 2048`、`kv_lora_rank 512`；`qk_nope_head_dim 192 + qk_rope_head_dim 64 = qk_head_dim 256`、`v_head_dim 256`、`head_dim 64`（= rope 维）。
- **Indexer（DSA）**：`GlmMoeDsaIndexer`（`indexer.py:51`），`index_n_heads 32`、`index_head_dim 128`、`index_topk 2048`、`indexer_rope_interleave True`。每 q token 由 Indexer 选出 TopK=2048 个相关 kv 后再算注意力。
- **算子路径**：先按 `cp_size > 1 and is_prefill` 选择 `forward_absorb_cp`，否则选择 `forward_absorb`；两者是替代分支，各自在内部准备 Q/KV，并执行 MLAProlog、稀疏注意力和 Epilog，不串行调用。算子层面见 [mla-prolog](../kernels/mla_prolog.md)、[sparse-flash-attention](../kernels/sparse_flash_attention.md)、[lightning-indexer](../kernels/lightning_indexer.md)。

## MoE（256 路由 + 1 共享，TopK=8）

`GlmMoeDsaMoE`（`modeling_glm.py:186`）：256 routed + 1 shared expert，每 token 选 8 个路由专家（`top_k + shared = 9` 激活），`routed_scaling_factor 2.5`。

- **路由**：`scoring_func=sigmoid`（`logits.sigmoid()`，`:291`）+ `topk_method=noaux_tc`（无辅助损失均衡，`:258`）。`n_routed_experts ∈ [256, 384]` 时走融合算子 `npu_moe_gating_top_k`（`norm_type=1` 即 sigmoid，`:276`）。

## Notes

- **与 V3.2-Exp 的关系**：GLM-5 是 cann-recipes 基于 GLM-5 开源代码迁移到 CANN 的样例，结构与方案均沿用 [deepseek-v3.2-exp](deepseek_v3_2_exp.md)；DSA / MoE / 量化 / 并行的完整机理与图示见 [deepseek-v3.2-exp](deepseek_v3_2_exp.md)，此处记 GLM-5 的规格差异与部署配置。
- **355B 变体**：官方称 GLM-5 从 355B-A32B 扩展到 744B-A40B，但 HF 仅发布 744B/40B 检查点（`zai-org/GLM-5` + `zai-org/GLM-5-FP8`）；355B-A32B 未作为独立 HF 仓发布。`zai-org/GLM-5.1` 是另一发布检查点，不别名到本文件。

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/glm_5_deployment.md)：配置、开关、失效条件与回退入口。
- [GLM-5 A3 W8A8 Decode 的来源性能观测](../../optimizations/benchmark_observations/glm5_a3_source_benchmark.md)：固定来源自报，未经本仓独立复测。

## Source basis

cann-recipes-infer @ **2c45117**（Atlas A3 部署事实）：

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/glm-5/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/README.md)（概述、硬件要求、权重转换、Benchmark）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/glm-5/config/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/config/README.md) + [`config/glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/config/glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml) + [`config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml)（部署规格）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/glm-5/models/{modeling_glm,configuration_glm,indexer,offload_cache}.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/models/modeling_glm.py)（DSA 注意力、MoE EP、MC2、量化、MTP、Offload 调用入口）
- stock HF 架构基线：`zai-org/GLM-5/config.json` + HuggingFace transformers `glm_moe_dsa`（verified 2026-05-15）

## Links

- [deepseek-v3.2-exp](deepseek_v3_2_exp.md)
- [dsa](../modules/dsa.md)
- [mla](../modules/mla.md)
- [lightning-indexer](../modules/lightning_indexer.md)
- [sparse-flash-attention](../kernels/sparse_flash_attention.md)
- [lightning-indexer](../kernels/lightning_indexer.md)
- [mla-prolog](../kernels/mla_prolog.md)
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)
- [double-routing](../techniques/double_routing.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [context-parallel](../parallelism/context_parallel.md)
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [kvcache-offload](../techniques/kvcache_offload.md)
- [w8a8c8](../quantization/w8a8c8.md)
- [npu-graph-mode](../techniques/npu_graph_mode.md)
- [weight-nz](../techniques/weight_nz.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [indexer-prolog](../kernels/indexer_prolog.md)（GLM-5 indexer 前处理 Q/Weight 多流切流 "22"/"33"）
