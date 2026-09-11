---
type: Concept
title: GLM-5
description: GLM-5 是智谱（Z.ai）744B-A40B MoE 大模型，网络结构与 DeepSeek-V3.2-Exp 完全一致（DSA：MLA 主干 + Lightning Indexer 稀疏选择），cann-recipes-infer 在 Atlas A3 上的并行策略与性能优化方案直接沿用 V3.2-Exp。覆盖 GlmMoeDsaForCausalLM 规格（78 层、6144 hidden、256 路由+1 共享专家 top-8）、DSA 注意力（MLAProlog + MLA 吸收 + GlmMoeDsaIndexer index_topk 2048 + CP 路径）、MoE EP 三路实现（double-routing / dispatch_v2+combine_v2 + 独立通信域 fullmesh_v2 / multi-stream）、sigmoid+noaux_tc 路由、W8A8C16 量化、CP 长序列(65536)+Attention DP、Embed/LMHead TP16、MoE EP 64/128、MTP3、KVCache Offload。Atlas A3 W8A8 decode 64 chips TPOT 22.54ms / 177.46 tokens/p/s。
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
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a3
---

# GLM-5

## Summary

GLM-5 是智谱（Z.ai）发布的 MoE 大模型，总参 **744B / 激活 40B**（官方称 GLM-5 系列从 355B-A32B 扩展到 744B-A40B；HuggingFace 仅发布 `zai-org/GLM-5`（744B/40B）与 `zai-org/GLM-5-FP8` 两份权重）。其网络结构与 [deepseek-v3.2-exp](deepseek_v3_2_exp.md) **完全一致**——同款 DeepSeek Sparse Attention (DSA)：MLA 主干 + Lightning Indexer 稀疏选择；因此 cann-recipes-infer 在 GLM-5 上的**并行策略与性能优化方案均直接沿用 V3.2-Exp**（README 明述）。

cann-recipes-infer 在 **Atlas A3** 集群上的 GLM-5 部署涉及：模型规格（`glm_moe_dsa`）、DSA 注意力算子谱系、MoE EP 三路实现、W8A8C16 量化、CP 长序列 + Attention DP 并行、MTP3 与 KVCache Offload。算子机理与 DSA 计算流的完整展开见 [deepseek-v3.2-exp](deepseek_v3_2_exp.md) 与各 module / kernel 页。

- **平台限定**：仅 Atlas A3 系列（镜像 `cann8.5_pt2.8.0_glm_aarch_image_v0.1`，驱动 Ascend HDK 25.2.0）。两 die 一卡，`world_size = 2 × chip_num`。见 [atlas-a3](../platforms/atlas_a3.md)。
- **结构同源**：`GlmMoeDsaForCausalLM`（`model_type=glm_moe_dsa`）的 DSA / MoE / 量化算子谱系与 V3.2-Exp 同构，差异仅在超参（vocab、层数、head 维、MoE 专家数等）。

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

| 维度 | 值 |
| MoE | 值 |
| ---- | ---- | ---- | ---- | ---- |
| vocab | 154880 |
| n_routed_experts | 256 |
| hidden | 6144 |
| n_shared_experts | 1 |
| n_layers | 78 |
| num_experts_per_tok | 8 |
| dense intermediate | 12288 |
| routed_scaling_factor | 2.5 |
| moe_intermediate | 2048 |
| n_group / topk_group | 1 / 1 |
| dense 层 | 1-3（共 3）| | scoring | sigmoid |
| MoE 层 | 4-78（共 75）| | balance | noaux_tc（无辅助损失）|
| max_position_embeddings | 202752 |
| norm_topk_prob | True |
| rms_norm_eps | 1e-5 |
| tie_word_embeddings | False |

> 层类型由 `GlmMoeDsaConfig` 硬编码 `mlp_layer_types = ["dense"]×3 + ["sparse"]×75`，不通过 `first_k_dense_replace` 配置。

## DSA 注意力（MLA + Indexer）

GLM-5 的注意力是 `GlmMoeDsaAttention`（`modeling_glm.py:661`），即 V3.2-Exp 同款 DSA（MLA + Lightning Indexer），算子机理见 [dsa](../modules/dsa.md)、[mla](../modules/mla.md)、[lightning-indexer](../modules/lightning_indexer.md)。

- **MLA 维度**：MHA（`num_attention_heads = num_key_value_heads = 64`）。`q_lora_rank 2048`、`kv_lora_rank 512`；`qk_nope_head_dim 192 + qk_rope_head_dim 64 = qk_head_dim 256`、`v_head_dim 256`、`head_dim 64`（= rope 维）。
- **Indexer（DSA）**：`GlmMoeDsaIndexer`（`indexer.py:51`），`index_n_heads 32`、`index_head_dim 128`、`index_topk 2048`、`indexer_rope_interleave True`。每 q token 由 Indexer 选出 TopK=2048 个相关 kv 后再算注意力。
- **算子路径**：MLAProlog 走 `npu_mla_prolog_v3`（`mlaprolog_prefill:1032` / `mlaprolog_decode:1172`）→ MLA **吸收**计算 `forward_absorb`（`:923`）→ CP 路径 `forward_absorb_cp`（`:969`，仅 Prefill 长序列）。Prefill 与 Decode 统一走 Absorb（与 V3.2-Exp 方案三一致）。算子层面见 [mla-prolog](../kernels/mla_prolog.md)、[sparse-flash-attention](../kernels/sparse_flash_attention.md)、[lightning-indexer](../kernels/lightning_indexer.md)。

## MoE（256 路由 + 1 共享，TopK=8）

`GlmMoeDsaMoE`（`modeling_glm.py:186`）：256 routed + 1 shared expert，每 token 选 8 个路由专家（`top_k + shared = 9` 激活），`routed_scaling_factor 2.5`。

- **路由**：`scoring_func=sigmoid`（`logits.sigmoid()`，`:291`）+ `topk_method=noaux_tc`（无辅助损失均衡，`:258`）。`n_routed_experts ∈ [256, 384]` 时走融合算子 `npu_moe_gating_top_k`（`norm_type=1` 即 sigmoid，`:276`）。
- **EP 三路实现**（`forward:397`）：`moe_tp_size>1` → `moe_infer_tp`；否则按阶段分流——Prefill 走 `moe_infer_double_routing`（`:574`，用 `npu_moe_init_routing_v2` / `npu_moe_re_routing` / `npu_moe_finalize_routing`），Decode 走 `moe_infer_dispatch_combine`（`:610`，一体化融合算子）。
- **MC2 / dispatch-combine-v2**：`set_mc2_kwargs`（`:364`）取**独立通信域** `moe_ep_group_mc2`（`:1941`）+ `comm_alg "fullmesh_v2"`（`:381`）；Decode 调 `npu_moe_distribute_dispatch_v2`（`:624`）/ `npu_moe_distribute_combine_v2`（`:655`），`a8` 量化时 `quant_mode=2`。属 893d72e「独立通信域 + fullmesh_v2」清单内。见 [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)、[double-routing](../techniques/double_routing.md)、[expert-parallel](../parallelism/expert_parallel.md)。
- **多流**：shared expert 与路由专家 Gating/Dispatch 无依赖，经 `npu_stream_switch` + tagged event 并发掩盖（`:407-418`），由 `enable_multi_streams: True` 使能。思想见 V3.2-Exp 页多流章节。

## 量化（W8A8C16）

- FP8 原始权重经 `utils/weight_convert.sh --quant_mode w8a8c16` 转为 **Int8** 权重，KVCache 维持 **C16**（BF16）。脚本同时支持 `bfloat16 / w8a8c16 / w8a8c8 / w4a8c8` 四种模式（后两者复用 V3.2-Exp 的量化参数包），但 GLM-5 的 benchmark 配置（`config/*.yaml` + README）走 **W8A8（w8a8c16）** 路径。
- **MoE 量化**：`gmm_quant_mode` 支持 `w8a8int8` / `w4a8int4`；W4A8 时 expert GMM `bias=True`（`:224`）。
- **激活/SwiGLU 算子**：`npu_dequant_swiglu_quant`（量化路径，`GlmMoeDsaMLP.forward_w8a8int8:120`）/ `npu_swiglu`（非量化，`:117`）。
- 量化机理（逐模块策略、精度评测）与 V3.2-Exp 同构，见 [w8a8c8](../quantization/w8a8c8.md) 及 V3.2-Exp 页量化章节。

## 并行与部署（Atlas A3）

部署 YAML 均 `exe_mode: ge_graph`（[npu-graph-mode](../techniques/npu_graph_mode.md)），`world_size = 2 × chip_num`。Int8 Prefill / Decode 均支持 **8-128 卡**（README）。

| 阶段 | YAML | world_size | cp_size | attn_tp | oproj_tp | dense_tp | moe_tp | embed/lmhead_tp | batch | input_max_len |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Prefill | `glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml` | 64 | 64 | 1 | 1 | 1 | 1 | 16 | 64 | 65536 |
| Decode | `glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml` | 128 | 128 | 1 | 4 | 4 | 1 | 16 | 256 | 65536 |

- **CP（长序列）**：`cp_size` 仅 Prefill 生效且 `cp_size = world_size`（长序列 65536，数据集 InfiniteBench `longbook_qa_eng`）；Decode 不启 CP。多 rank 均摊长序列 Attention 计算降低 TTFT，机理见 [context-parallel](../parallelism/context_parallel.md)。
- **Attention DP**：`attn_tp_size=1` 即 attention 数据并行；`oproj_tp_size` 独立切（仅 `attn_tp_size==1` 时支持）——Decode 取 `oproj_tp 4 / dense_tp 4`，Prefill 取 1。
- **Embed / LMHead TP**：`embed_tp_size = lmhead_tp_size = 16`（A3 单 node 8 卡 × 2 die = 16，TP 域控制在 HCCS 内）。
- **MoE EP**：64ep（Prefill）/ 128ep（Decode），`moe_tp_size=1`。
- **其它**：`enable_weight_nz: True`、`pa_block_size: 128`（见 [weight-nz](../techniques/weight_nz.md)）、`enable_multi_streams: True`、`enable_online_split_weight: True`、`perfect_eplb` 可选。

## MTP（next_n=3）

`GlmMoeDsaModelMTPLayer`（`modeling_glm.py:1693`）+ `GlmMoeDsaForCausalLM(is_mtp)`（`:1748`）。`next_n` 支持 0-3，两份 benchmark yaml 均设 `next_n: 3`（MTP3）。Benchmark 注：MTP3 + perfect eplb，平均 3 个 draft token 中 accept **1.44** 个。机理见 [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)。

> stock HF 的 `glm_moe_dsa` 建模路径不含 MTP 头（config 的 `num_nextn_predict_layers` 未被读取）；cann-recipes 的 MTP 是部署侧的投机解码实现，与 V3.2-Exp 同款。

## KVCache Offload（长序列）

长序列 KVCache 经 `offload_cache.OffloadCache`（`modeling_glm.py:54` 引入，attention forward 透传 `offload_cache`）卸载到 Host 内存以提升 batch。机理与 V3.2-Exp 一致（Decode 用相邻 token TopK 命中率复用设备端 cache），见 [kvcache-offload](../techniques/kvcache_offload.md)。

## Benchmark

基于 Atlas A3，`config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml`，MTP3 + perfect eplb：

| Quant Mode | Global Batch | Seq Length | Chips | TPOT (ms) | Throughput (tokens/p/s) |
| ---- | ---- | ---- | ---- | ---- | ---- |
| W8A8 | 256 | 65536 | 64 | 22.54 | 177.46 |

> 平均 3 个 draft token 中 accept 1.44 个。

## Notes

- **与 V3.2-Exp 的关系**：GLM-5 是 cann-recipes 基于 GLM-5 开源代码迁移到 CANN 的样例，结构与方案均沿用 [deepseek-v3.2-exp](deepseek_v3_2_exp.md)；DSA / MoE / 量化 / 并行的完整机理与图示见 [deepseek-v3.2-exp](deepseek_v3_2_exp.md)，此处记 GLM-5 的规格差异与部署配置。
- **355B 变体**：官方称 GLM-5 从 355B-A32B 扩展到 744B-A40B，但 HF 仅发布 744B/40B 检查点（`zai-org/GLM-5` + `zai-org/GLM-5-FP8`）；355B-A32B 未作为独立 HF 仓发布。`zai-org/GLM-5.1` 是另一发布检查点，不别名到本文件。

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