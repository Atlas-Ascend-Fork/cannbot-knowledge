---
type: Concept
title: DeepSeek-R1
description: DeepSeek-R1 的 MLA、共享与路由专家及模型结构；部署流程和性能数据分别引用规范入口。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_prefill_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-21T10:02:02Z'
platforms:
- a3
---



# DeepSeek-R1

## Summary

DeepSeek-R1 沿用 DeepSeek-V3 的 MLA + DeepSeekMoE 架构：低秩 KV 压缩、1个共享专家与256个路由专家、top-k=8。

本卡保留网络结构及其状态机制。R1 与 Kimi-K2-Thinking 的架构思路同源，但固定仓中的执行器与建模是不同文件/副本，不再表述为共用同一 modeling_deepseek.py。平台配置、开关和验收步骤见[模型部署流程](../../guides/models/deepseek_r1_deployment.md)，此处只保留模型机制。

## Architecture And Serving Traits

### Transformer Block 结构

```mermaid
flowchart TD
 In[Hidden] --> RN1[RMSNorm]
 RN1 --> MLA[MLA<br/>q_a_proj → q_a_layernorm → q_b_proj<br/>kv_a_proj_with_mqa → kv_a_layernorm → kv_b_proj<br/>RoPE + FA]
 MLA --> Add1[+ residual]
 Add1 --> RN2[RMSNorm]
 RN2 --> MoE[DeepSeekMoE<br/>shared expert × 1<br/>routed experts × 256, top-k=8]
 MoE --> Add2[+ residual]
 Add2 --> Out[Hidden']
```

### MLA (Multi-head Latent Attention)

低秩 KV 压缩，显著降低 KVCache 占用。Q 侧通过 `q_a_proj → q_a_layernorm → q_b_proj` 实现 low-rank→full-rank 的两级投影，KV 侧通过 `kv_a_proj_with_mqa → kv_a_layernorm → kv_b_proj` 压缩到 `kv_lora_rank`（通常 512）并 MQA 共享。RoPE 仅作用于 `qk_rope_head_dim` 通道。详见 [mla](../modules/mla.md)。

### MoE 结构

每层包含：

- **1 个 shared expert**：所有 token 都经过，提供稳定信号。
- **256 个 routed experts**：通过 `gate` + `topk=8` 选择，仅激活部分专家。
- **gate** 输出 `topk_idx` + `topk_weight`；在 Decode 使用 `npu_moe_gating_top_k` 融合算子。
- EP 部署下每卡分到 `256 / ep_size` 个 routed expert + 同时存放一个 shared expert 的完整副本。

## 架构图（stock HF 基线）

DeepSeek-R1 的 **stock HuggingFace 模型级架构**（部署前基线，拓扑按 HF `DeepseekV3ForCausalLM` modeling 整理，与 cann-recipes-infer @2c45117 自带 `configuration_deepseek.py` 默认值逐项一致）。R1 复用 DeepSeek-V3 的架构类（同 `architectures=DeepseekV3ForCausalLM`、`model_type=deepseek_v3`），故此基线即 V3/R1 共用拓扑。该模型级架构与昇腾 Atlas A3 部署优化（MLA-Prolog 融合、Double-Routing、micro-batch、量化、TorchAir 等）互补：一者描述「模型长什么样」，另一者描述「在 NPU 上怎么跑」。溯源见 [`deepseek-ai/DeepSeek-V3/config.json`](https://huggingface.co/deepseek-ai/DeepSeek-V3/blob/e815299b0bcbac849fa540c768ef21845365c9eb/config.json)。

> 此为模型级整图（input → embed → 61 个 block → 末层 RMSNorm → LMHead）；[Transformer Block 结构](#transformer-block-结构) 给出的是单个 block 内部（RMSNorm → MLA → MoE → 残差）的细节流程，两者层级互补、不冲突。

```mermaid
flowchart TD
    in([input tokens])
    in --> embed["Embed : V → 7168"]

    subgraph block ["Block × 61"]
        direction TB
        n1[RMSNorm]
        attn[MLA Attn]
        n2[RMSNorm]
        moe[MoE FFN]
        n1 --> attn
        attn -->|+ residual| n2
        n2 --> moe
    end

    embed --> n1
    moe -->|+ residual| fnorm[RMSNorm]
    fnorm --> head["LMHead : 7168 → V"]
    head --> logits([logits])
```

> 说明：Layer 1–3 使用 dense FFN，Layer 4–61 使用 MoE（config `first_k_dense_replace=3`）；图中只画了 MoE 路径（常见情形），前 3 层的 dense-FFN 替换未单独绘制。

关键参数（仅保留对部署有意义的行，取自 HF config）：

| 模块 | 参数 | 值 |
| ---- | ---- | ---- |
| — | n_layers | 61 |
| — | hidden | 7168 |
| — | vocab | 129280 |
| MLA | n_heads | 128 |
| MLA | q_lora_rank | 1536 |
| MLA | kv_lora_rank | 512 |
| MLA | qk_nope_head_dim | 128 |
| MLA | qk_rope_head_dim | 64 |
| MLA | v_head_dim | 128 |
| MoE | n_routed_experts | 256 |
| MoE | n_shared_experts | 1 |
| MoE | top_k | 8 |
| MoE | moe_intermediate | 2048 |
| MoE | dense_layers | 1–3 only |

其中 `kv_lora_rank=512`、`q_lora_rank=1536` 是 MLA 低秩压缩的两级 latent 维度（KVCache 仅存 `c_KV`=512 + 单份共享 `k_rope`=64），与 [MLA 部署流程](../../guides/models/deepseek_r1_deployment.md) 一节中 `npu_mla_prolog_v3` 的 Q/K/V 投影路径对应；`n_routed_experts=256` / `n_shared_experts=1` / `top_k=8` 与 [MoE 结构](#moe-结构) 一节一致。MLA 结构细节见 [mla](../modules/mla.md)，平台见 [atlas-a3](../platforms/atlas_a3.md)。

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/deepseek_r1_deployment.md)：配置、开关、失效条件与回退入口。
- [DeepSeek-R1 A3 Prefill 双流的来源性能观测](../../optimizations/benchmark_observations/deepseek_r1_a3_prefill_source_benchmark.md)：固定来源自报，未经本仓独立复测。
- [DeepSeek-R1 A3 Decode 的来源数据与 Chips 分歧](../../optimizations/benchmark_observations/deepseek_r1_a3_decode_source_benchmark.md)：固定来源自报，未经本仓独立复测。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-r1/deepseek_r1_prefill_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_prefill_optimization.md)（Prefill 优化主文档：MLA-DP/SP-TP-SP、Double-Routing、NTD、micro-batch、weightNZ）；`docs/models/deepseek-r1/deepseek_r1_decode_optimization.md`（Decode 优化主文档：通用优化、MLA 融合算子、MoE EP 融合算子、MLP 合并、TorchAir、MTP、AIV、SuperKernel、Benchmark）。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek_r1/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek_r1/README.md)（环境部署、权重转换、Benchmark、长序列 OOM 处理）；`models/deepseek_r1/config/*.yaml`（Prefill/Decode 各规模量化部署配置）；`models/deepseek_r1/models/modeling_deepseek.py`（`DeepseekV3Attention.forward_page_attention_mla_prolog`、`DeepseekV3MoE.forward_*`、`DeepseekV3Model.forward_microbatch_v1/v2`、SuperKernel scope 入口）；`models/deepseek_r1/utils/convert_model.py`（FP8 → BF16 / W8A8C16 / W8A8C8 权重转换）。

## Links

- [atlas-a3](../platforms/atlas_a3.md)
- [torchair](../frameworks/torchair.md)
- [ascendc](../frameworks/ascendc.md)
- [kv-cache-manager](../frameworks/kv_cache_manager.md)
- [mla](../modules/mla.md)
- [mla-prolog](../kernels/mla_prolog.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [data-parallel](../parallelism/data_parallel.md)
- [double-routing](../techniques/double_routing.md)
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)
- [prefill-micro-batch](../techniques/prefill_micro_batch.md)
- [sp-tp-sp](../parallelism/sp_tp_sp.md)
- [weight-nz](../techniques/weight_nz.md)
- [superkernel](../techniques/superkernel.md)
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [moe-multi-stream](../techniques/moe_multi_stream.md)
- [multi-stream](../techniques/multi_stream.md)（多流总纲：R1 是 decode 共享/路由专家 Cube↔Vector 互补 + prefill micro-batch 双流的代表样例）
- [w8a8c8](../quantization/w8a8c8.md)
- [deepseek-r1-rl](../../../training/guides/recipes/deepseek_r1_rl.md)（跨域·训练：R1 在 A3 128 卡的 veRL+MindSpeed+vLLM-Ascend 全共卡 GRPO RL 后训练，120+ TPS/卡；本推理部署是其训练目标模型）
- [grpo-dapo](../../../training/concepts/techniques/grpo_dapo.md)（跨域·训练：R1 RL 用 GRPO 算法）
- [eplb](../../../training/concepts/techniques/eplb.md)（跨域·训练：EPLB(DeepSeek 提出的专家并行负载均衡器)）
