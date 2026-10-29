---
type: Concept
title: Gemma-4-26B-A4B
description: Gemma-4 文本 Decoder 的混合滑窗/全局注意力、并联 Dense/MoE 与异构缓存机制。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/agentic/optimization_report.md
  role: supporting
created_at: '2026-05-31T00:00:00Z'
updated_at: '2026-10-22T10:36:46Z'
platforms:
- a3
---



# Gemma-4-26B-A4B

## Summary

Gemma-4-26B-A4B的本卡范围是文本Language MoE Decoder；视觉塔属于另一部分，不据文本部署推导已适配。30层包含5:1的sliding/full GQA，每层Dense MLP与MoE并联，词表Embedding与LMHead共享。

Sliding/full的head维度和K=V关系影响缓存形状；具体平台开关、图后端与质量验收由Guide维护。平台配置、开关和验收步骤见[模型部署流程](../../guides/models/gemma4_26b_a4b_deployment.md)，此处只保留模型机制。

## 架构（仅 Language Decoder）

Token Embedding（vocab=262144，与 LM Head 共享权重）→ Decoder Block ×30 → LM Head。每个 Decoder Block 内 **Dense MLP 与 MoE 并联**（非交替式）：

- **Dense MLP**：`gate/up/down`，intermediate=2112，激活 GELU（代码 `Gemma4MLP.forward` 走 `npu_fast_gelu(gate) * up`，等价 `gelu(approximate='tanh')`）。
- **MoE**：128 experts，top-8，moe_intermediate=704，专家激活 **GEGLU**（`Gemma4GegluMoEGMM`）。
- 多组 LayerNorm（基础 4：input / post_attention / pre_feedforward / post_feedforward；MoE 分支再 +3）+ layer_scalar。

### 双模式 Attention（核心）

由 `layer_types` 5:1 模式划分（`sliding_window_pattern=6`，`(i+1)%6!=0` 为 sliding，最后一层强制 full）：

| 模式 | 层数 | N_h | N_kv | head_dim | 其他 |
|---|---|---|---|---|---|
| Sliding | 25 | 16 | 8 | 256 | GQA，`window=1024` |
| Full | 5 | 16 | 2 | 512 | GQA，`k_eq_v=True`（K/V 共享一组投影，无独立 v_proj）|

- `Gemma4Attention.use_k_eq_v = attention_k_eq_v and not is_sliding`：仅 full 层 K=V，省 v_proj。
- QK RMSNorm 已对 Q/K 归一化，故 FA 调用使用 **`scale=1.0`**（标准 `1/√d` 缩放会让 attention 过平坦、不匹配 reference）。
- Full 层 N_kv=2 据优化报告与部署（`num_global_key_value_heads=2`）；`configuration_gemma4.py` 默认 `num_global_key_value_heads=None` 回退 `num_key_value_heads`(=8)，full 层实际值由外部 HF config 提供、源内未直接给出，按报告/部署计 2（待验证）。

## 异构连续缓存（KVCache）

双模式 Attention 导致 KV 维度异构：sliding 层 `kv_dim = N_kv×head_dim = 8×256 = 2048`；full 层 `2×512 = 1024`（单份 K 或 V 的宽度；k_eq_v 共享投影权重，不共享缓存）。投影结果 clone 后，K/V 分别归一化，且仅 K 施加 RoPE，随后分别写入 k_cache/v_cache；内存预算不能把两份缓存合并。Gemma-4 采用**连续缓存（非 Paged）**：

- 每层独立分配缓冲（`cache_unit = N_kv×head_dim`），sliding/full shape 不同，避免统一 Paged-Attention block 格式维护两套 block_table 的复杂度。
- `attn_tp=1` 无 KV head 切分需求，连续缓存足够。

与 [kv-cache-manager](../frameworks/kv_cache_manager.md) 的框架级块式 Paged Attention 不同——该 KVCacheManager 抽象 FullAttention/SlidingWindow 两类 block 策略；Gemma-4 走模型自管的连续缓存路径。

## FA 与 RoPE

- FA 走 **FIA v1**（[fused-infer-attention-score](../kernels/fused_infer_attention_score.md) `npu_fused_infer_attention_score`，输入布局 BSH）；仅 `ge_graph` Decode 用 `tng.ops` 同名算子；`npugraph_ex` 和 Prefill 使用 `torch.ops.npu` 同名算子。
- Sliding 层 Prefill/Decode：`sparse_mode=4` + `pre_tokens=sliding_window(1024)`（即 sliding window）；Full 层按阶段不同：Prefill `sparse_mode=3`（标准 causal，`pre_tokens=INT32_MAX`）、Decode `sparse_mode=0`（`pre_tokens=INT32_MAX`，`modeling_gemma4.py:789-822`）。
- Sliding 全维 RoPE 用 `npu_rotary_mul`（`rotary_mode='half'`）；Full 层 **partial RoPE**（`partial_rotary_factor=0.25`，rotary_dim=128）用 slice + `npu_rotary_mul` + cat 包装实现（`npu_rotary_mul` 无原生 partial 支持，见算子 gap）。

## 架构图（stock HF 基线）

下图为 Gemma-4-26B-A4B-it 的 **stock HF 架构基线**（部署前先验），拓扑由 HF `config.json` + `transformers` `modeling_gemma4.py` 合成，与上述昇腾 NPU 部署优化（[npu-graph-mode](../techniques/npu_graph_mode.md) 图模式 / [expert-parallel](../parallelism/expert_parallel.md) MoE EP 双路径 / 异构连续缓存等）互补——前者是结构先验，后者是部署落地。溯源：`google/gemma-4-26B-A4B-it/config.json` + `huggingface/transformers` `src/transformers/models/gemma4/modeling_gemma4.py`。

> 视觉塔（ViT）/ Multimodal Embedder / audio_config / fusion 节点不在覆盖范围内（仅覆盖 Language MoE Decoder，参见上文「架构（仅 Language Decoder）」）；下图已裁剪至文本 MoE backbone 的 block-level 流程，去除了原图的视觉/融合分支。

```mermaid
flowchart TD
    in([input tokens]) --> embed["Embed : V → 2816<br/><i>tied to LMHead</i>"]

    subgraph block ["Block × 30"]
        direction TB
        n1[RMSNorm]
        attn["GQA Attn<br/><i>sliding or full per layer_types</i>"]
        n2[RMSNorm]
        pren1[RMSNorm]
        mlp["Dense MLP<br/><i>shared path · intermediate 2112</i>"]
        pren2[RMSNorm]
        router["Router<br/><i>top-8 of 128</i>"]
        moe["Routed Experts<br/><i>intermediate 704 · 8 active</i>"]
        postn1[RMSNorm]
        postn2[RMSNorm]
        sum((Σ))
        n1 --> attn
        attn --> n2
        n2 -->|+ residual| pren1
        n2 -->|+ residual| pren2
        pren1 --> mlp --> postn1 --> sum
        pren2 --> router --> moe --> postn2 --> sum
    end

    embed --> n1
    sum -->|+ residual| fnorm[RMSNorm]
    fnorm --> head["LMHead : 2816 → V<br/><i>tied to Embed</i>"]
    head --> logits([logits])
```

精简关键参数（取自 `google/gemma-4-26B-A4B-it/config.json` · Text backbone，仅保留对部署有意义的行）：

| 模块 | 参数 | 值 |
|---|---|---|
| — | n_layers | 30 |
| — | hidden | 2816 |
| — | vocab / tie_word_embeddings | 262144 / true（Embed 与 LMHead 共享权重）|
| GQA-sliding | n_q / n_kv / head_dim / window | 16 / 8 / 256 / 1024 |
| GQA-full | n_q / num_global_key_value_heads / global_head_dim | 16 / 2 / 512 |
| GQA-full | attention_k_eq_v | true（K/V 共享投影，`v_proj=None`）|
| Dense MLP | intermediate / 激活 | 2112 / gelu_pytorch_tanh |
| MoE | num_experts / top_k / moe_intermediate | 128 / 8 / 704 |
| RoPE-full | partial_rotary_factor / rope_type | 0.25（25% dims 旋转）/ proportional |
| RoPE | rope_theta（sliding / full） | 10,000 / 1,000,000 |
| — | layer_types 周期 | cycle 6 = 5×sliding + 1×full（full 层 idx 5/11/17/23/29）|

注：图的 HF `config.json` 给出 full 层 `num_global_key_value_heads=2`，与正文报告/部署值（N_kv=2）一致——印证了上文「待验证」的取值（源默认回退 8；此处 HF config 确认为 2）。

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/gemma4_26b_a4b_deployment.md)：配置、开关、失效条件与回退入口。
- [Gemma-4 A2 图模式的两组来源性能口径](../../optimizations/benchmark_observations/gemma4_a2_source_benchmark.md)：固定来源自报，未经本仓独立复测。
- [Gemma-4 A3 图后端与 EP 路由的来源观测](../../optimizations/benchmark_observations/gemma4_a3_source_benchmark.md)：固定来源自报，未经本仓独立复测。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/gemma4_26b_a4b/agentic/optimization_report.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/agentic/optimization_report.md)（§1.1 架构、§3 并行、§4 KVCache/FA/RoPE、§5 融合、§6 图模式 + §6.3 mc2 vs local_experts、§7 A2↔A3、§8 累计、§9 算子需求、§10 未覆盖项）+ [`README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/README.md)（概述 / 规模 / Agent 工作流 / 产品型号 / CANN 8.5.0）。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/gemma4_26b_a4b/models/modeling_gemma4.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/models/modeling_gemma4.py)（`Gemma4SparseMoeBlock` `moe_ep_decode_mode`/`default_mode` L385-386、`moe_infer_local_experts` L596-645、`Gemma4Attention.use_k_eq_v` L679 / FA `sparse_mode` L789-822 / `npu_rotary_mul` L766-768、`Gemma4MLP` `npu_fast_gelu` L243、`_GegluMoEMethod` L282-318）+ [`models/configuration_gemma4.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/models/configuration_gemma4.py)（vocab=262144/layers=30/N_kv=8/head_dim=256/global_head_dim=512/sliding_window=1024/partial_rotary_factor=0.25/layer_types 5:1）+ [`config/gemma4_rank_8_8ep_gegraph_decode.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/config/gemma4_rank_8_8ep_gegraph_decode.yaml)（EP8/attn_tp=1/embed_tp=8/lmhead_tp=8/`moe_ep_decode_mode: local_experts`）。
- 提交 `feat: add gemma-4 model optimized by agent skills`（16e3806，基线 2f82d10 后新增；README/config 修复见 690451d）。Agent 迁移来路：`model-infer-optimize` Agent Skills 自动完成全流程优化（来路记于此，非正文性能归因）。

## Links

- [atlas-a3](../platforms/atlas_a3.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [data-parallel](../parallelism/data_parallel.md)
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)
- [npu-graph-mode](../techniques/npu_graph_mode.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [kv-cache-manager](../frameworks/kv_cache_manager.md)
- [cann-executor](../frameworks/cann_executor.md)
- [inference-config](../techniques/inference_config.md)
