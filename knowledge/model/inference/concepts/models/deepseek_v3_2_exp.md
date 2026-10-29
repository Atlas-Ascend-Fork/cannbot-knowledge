---
type: Concept
title: DeepSeek-V3.2-Exp
description: DeepSeek-V3.2-Exp 的 DSA、MLA 与 Indexer 状态机制；部署、量化和性能各归对应入口。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-21T10:02:02Z'
platforms:
- a3
---




# DeepSeek-V3.2-Exp

## Summary

DeepSeek-V3.2-Exp 在V3.1谱系的MLA/MoE主干上增加Lightning Indexer，以TopK选择参与计算的历史KV。稀疏计算不等于删除完整MLA缓存：还需要Indexer Key Cache。

本卡描述结构和状态，AscendC、PyPTO、TileLang的部署实现不因同属DSA就可互换。平台配置、开关和验收步骤见[模型部署流程](../../guides/models/deepseek_v3_2_exp_deployment.md)，此处只保留模型机制。

## Architecture And Serving Traits

### DeepSeek-V3.2-Exp vs V3.1

> 源："相较 DeepSeek-V3.1，DeepSeek-V3.2-Exp 主要新增了 Lightning Indexer 稀疏模块，旨在从长序列中稀疏选择 Topk 个 Token 用于计算注意力。"

- **权重内存新增**：Lightning Indexer 是类 MQA 结构，新增 `q_b_proj`、`wk_proj`、`weight_proj` 三个 Linear，综合所有 Layer 约 **+0.85B** 参数。
- **KVCache 内存新增**：在保留完整 MLA Full KVCache 的基础上，额外缓存 **Indexer Key Cache**：
 `batch_size × kv_length × Indexer_head_dim × storage_bytes × num_layers`。每 rank 4batch × 64K、BF16 场景新增约 **4 GB**。
- **Prefill MLA计算流**：本固定实现使用Absorb与稀疏Attention；三种候选的BMM形状与访存推导见[权重吸收规则](../../optimizations/rules/mla_weight_absorption_latent_kv.md)，阶段/序列取舍见[DSA选型规则](../../optimizations/rules/dsa_sparse_prefill_mla_scheme_by_seqlen.md)。

### DSA 计算流

DSA 可分为 5 个阶段：

![DSA 融合范围](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/kernel_scope.jpg)
*来源：[`docs/models/deepseek-v3.2-exp/figures/kernel_scope.jpg`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/kernel_scope.jpg)（cann-recipes-infer @ 2f82d10）*

```mermaid
flowchart LR
 In[Hidden] --> MLAP[MLAProlog<br/>Q/KV LoRA + RoPE + Norm<br/>MLA KVCache 写入]
 In --> IP[IndexerProlog<br/>Indexer Q/K proj<br/>Hadamard + 动态量化<br/>Indexer KCache 写入]
 IP --> LI[Lightning Indexer<br/>BatchMatmul Q@K^T + ReLU<br/>× W (GQA-sum) + Top-K 2048]
 LI --> SFA[Sparse Flash Attention<br/>Gather TopK KV + FA]
 MLAP --> SFA
 SFA --> Ep[MLAEpilog<br/>O_proj + V 升维]
```

见 [sparse-flash-attention](../modules/sparse_flash_attention.md)、[lightning-indexer](../modules/lightning_indexer.md) 展开每个模块的计算语义；算子层面见 [lightning-indexer](../kernels/lightning_indexer.md)、[sparse-flash-attention](../kernels/sparse_flash_attention.md)、[indexer-prolog](../kernels/indexer_prolog.md)、[deepseek-indexer-attention](../kernels/deepseek_indexer_attention.md)。

## Future Plan

固定来源的低比特/KV压缩、跨层预取与MegaKernel是来源计划，不当作已落地能力。适配与验证边界见模型Guide。

## 架构图（stock HF 基线）

这是 DeepSeek-V3.2-Exp 的 **stock HF 架构**（部署前基线，源自 HF `config.json` + 自带 `inference/model.py` 核实），刻画 ×61 层 block 级前向拓扑与原始模型规格，与本页其余面向 NPU 部署的优化（DSA 融合算子、CP/EP 并行、量化、Offload 等）互补——前者是模型先验，后者是 cann-recipes-infer 在 [atlas-a3](../platforms/atlas_a3.md) 上的部署改造。模型主体即 [mla](../modules/mla.md) + [lightning-indexer](../modules/lightning_indexer.md) 构成的 DSA 注意力（详见上文「DSA 计算流」）。

> 溯源：`deepseek-ai/DeepSeek-V3.2-Exp/config.json`（verified 2026-05-15，`architectures=["DeepseekV32ForCausalLM"]`、`model_type=deepseek_v32`）+ `deepseek-ai/DeepSeek-V3.2-Exp/inference/model.py`（verified 2026-05-15，自带定制推理代码，无标准 HF `modeling_*.py`）。

```mermaid
flowchart TD
    in([input tokens])
    in --> embed["Embed : V → 7168"]

    subgraph block ["Block × 61"]
        direction TB
        n1[RMSNorm]
        attn["DSA Attn<br/><i>MLA + lightning indexer</i>"]
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

注意力模块标注为 **DSA Attn**：在自带 `inference/model.py` 中 indexer 作为 `self.indexer` 实例化于 `MLA` 类内、由 `MLA.forward` 调用，indexer 输出的 TopK index 转为 pre-softmax 加性 mask（`scatter(−inf, topk_indices, 0)` 加到 raw attention score 上）。位置 5 的 FFN 按层号交替：第 1–3 层为 dense FFN、第 4–61 层为 MoE FFN（`first_k_dense_replace=3`）。

### 关键参数（stock HF config）

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
| Indexer | index_n_heads | 64 |
| Indexer | index_head_dim | 128 |
| Indexer | index_topk | 2048 |
| MoE | n_routed_experts | 256 |
| MoE | n_shared_experts | 1 |
| MoE | top_k | 8 |
| MoE | moe_intermediate | 2048 |
| MoE | dense_layers | 仅第 1–3 层 |
| RoPE | yarn factor | 40（`original_max_pos=4096`） |
| — | max_position_embeddings | 163840 |

> stock HF 的 `inference/model.py` 仅有单个输出 head，`config.json` 的 `num_nextn_predict_layers=1` 在该自带推理代码中**未落地**（无 MTP/NextNPredictor 类）；而本页上文记录的 `next_n: 3`（MTP3）是 cann-recipes-infer 的 NPU 部署在自研 executor 框架下另行实现的推测解码，二者描述不同制品（stock HF 推理 vs. NPU 部署），互补而非冲突。MoE 规格（256+1、top-8、`moe_intermediate=2048`、`noaux_tc`）与 DeepSeek-V3 完全一致，区别仅在注意力身份由 `mla` 变为 `dsa`（MLA + lightning indexer），见 [deepseek-r1](deepseek_r1.md) 的 V3 谱系与 [deepseek-v4](deepseek_v4.md) 的后继 DSA/MQA 演进。

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/deepseek_v3_2_exp_deployment.md)：配置、开关、失效条件与回退入口。
- [DeepSeek-V3.2-Exp A3 时延、吞吐与容量的来源观测](../../optimizations/benchmark_observations/deepseek_v32_a3_source_benchmark.md)：固定来源自报，未经本仓独立复测。
- [量化精度观测草稿](../../optimizations/benchmark_observations/benchmark_deepseek_v32_quant_accuracy.md)：保留两组基线，未完成人工精度验收。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md)（推理总览、并行、MTP、量化、多流、Offload、Benchmark、Future Plan）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_ascendc_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_ascendc_operator_guide.md)（AscendC LI + SFA 融合算子）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md)（PyPTO Indexer Prolog / Deepseek Indexer Attention / Lightning Indexer）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md)（TileLang NPU 适配 + LI/SFA 实现）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v3.2-exp/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek-v3.2-exp/README.md)、`config/*.yaml`（部署规格与环境）、`models/{modeling_deepseek,indexer,offload_cache,model_infer}.py`（调用入口）

## Links

- [atlas-a3](../platforms/atlas_a3.md)
- [ascendc](../frameworks/ascendc.md)
- [pypto](../frameworks/pypto.md)
- [tilelang](../frameworks/tilelang.md)
- [torchair](../frameworks/torchair.md)
- [mla](../modules/mla.md)
- [sparse-flash-attention](../modules/sparse_flash_attention.md)
- [lightning-indexer](../modules/lightning_indexer.md)
- [dsa](../modules/dsa.md)（DSA 顶层架构模式 = MLA 子图 + indexer overlay，V3.2-Exp 是核心验证实例）
- [mla-prolog](../kernels/mla_prolog.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [lightning-indexer](../kernels/lightning_indexer.md)
- [sparse-flash-attention](../kernels/sparse_flash_attention.md)
- [indexer-prolog](../kernels/indexer_prolog.md)
- [deepseek-indexer-attention](../kernels/deepseek_indexer_attention.md)
- [gather-selection-kv-cache](../kernels/gather_selection_kv_cache.md)
- [context-parallel](../parallelism/context_parallel.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [data-parallel](../parallelism/data_parallel.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [kvcache-offload](../techniques/kvcache_offload.md)
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [moe-multi-stream](../techniques/moe_multi_stream.md)
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)
- [weight-nz](../techniques/weight_nz.md)
- [zigzag-cp](../parallelism/zigzag_cp.md)
- [w8a8c8](../quantization/w8a8c8.md)
- [w4a8c8](../quantization/w4a8c8.md)
- [deepseek-r1](deepseek_r1.md)
- [deepseek-v4](deepseek_v4.md)（后继 DeepSeek-V4 —— DSA/LI 谱系延续，attention 主体由 MLA 改为 MQA/Shared-KV + 滑窗/压缩交错）
- [glm-5](glm_5.md)（GLM-5 结构与本模型一致，cann-recipes 部署方案直接沿用 V3.2-Exp）
- [hixl](../techniques/hixl.md)（长序列 KVCache 卸载 DRAM 后 NPU↔DRAM 高性能传输经 HIXL 单边零拷贝）
- [multi-stream](../techniques/multi_stream.md)（共享专家双流 / Indexer 前处理多流 / KVCache 异步流的方法论总纲）
- [deepseek-v32-pretrain](../../../training/guides/recipes/deepseek_v32_pretrain.md)（跨域：训练侧 DeepSeek-V3.2 TorchTitan 32K 长序列预训练 —— DSA 反向 SLIG/SFAG、自定义 CP for DSA、FSDP2 极致显存部署）
