---
type: Concept
title: Kimi-K2-Thinking
description: Kimi-K2-Thinking 的 MLA/MoE 谱系、64 Attention heads 与原生混合精度边界。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/kimi-k2-thinking/kimi_k2_thinking_inference_guide.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-21T10:02:02Z'
platforms:
- a3
---



# Kimi-K2-Thinking

## Summary

Kimi-K2-Thinking 与Kimi-K2同属MLA/DeepSeekMoE谱系，保留共享与路由专家；其Attention为64 heads，不能仅据head减少认定投机解码必然更快。MoE W4A16与Attention BF16是该实践采用的不同模块精度。

R1同族机制可参考，但固定仓中的Kimi runner/建模为独立legacy副本，不能直接继承全部R1开关。平台配置、开关和验收步骤见[模型部署流程](../../guides/models/kimi_k2_thinking_deployment.md)，此处只保留模型机制。

## Architecture And Serving Traits

Kimi-K2-Thinking 与 DeepSeek-V3 / DeepSeek-R1 / Kimi-K2 同属 MLA + DeepSeekMoE 架构族，Transformer Block 结构与 [deepseek-r1](deepseek_r1.md) 基本一致（MLA + shared expert + routed experts，同款 DeepseekV3 架构类；但 Kimi 的 `modeling_deepseek.py` 是独立适配副本，**非与 R1 同一文件**）。关键差异：

- **Attention Head数量**：Kimi-K2-Thinking为64，相对DeepSeek V3.1的128减少；head数是结构差异，不作为性能承诺。
- **原生 W4A16 MoE + BF16 Attention**：Kimi-K2-Thinking 原生量化模式，MoE `GroupedMatmul` 采用 W4A16 计算，Attention 保留 BF16 精度模式。**不支持 W8A8C8**（见 [w8a8c8](../quantization/w8a8c8.md)）。
- **独立代码副本（legacy 路径，非共用 R1 文件）**：Kimi 走 legacy ModelRunner 部署模式，`models/kimi-k2-thinking/` 自带整套副本——`infer.py` + `runner_deepseek.py`（`DeepSeekRunner` 类）+ `models/{modeling_deepseek,configuration_deepseek,model_infer,modules}.py`。其 `modeling_deepseek.py`（@2f82d10 实测 2381 行）与 R1 的（`models/deepseek_r1/models/modeling_deepseek.py`，@2f82d10 实测 2761 行；R1 走新执行器、无 `runner_deepseek.py`/`infer.py`）为**不同文件**——共享的是 DeepseekV3 架构与优化思路，而非源文件本身。

## Future Plan

来源把Attention低比特量化与进一步长序列优化列为计划，不作为当前实现能力；验收边界见Guide。

## 架构图（stock HF 基线）

下图与参数为 **Kimi-K2 stock HF 架构**（部署前基线，源自 HF config + 复用的 `DeepseekV3ForCausalLM` modeling 类核实），与本页其余的 NPU 部署优化互补：前者是部署无关的网络拓扑先验，后者描述昇腾平台上的并行/量化/融合 Kernel 落地。**该图是 Kimi-K2 基线结构**——Kimi-K2-Thinking 与 Kimi-K2 同属 `DeepseekV3ForCausalLM` 拓扑（见 [deepseek-r1](deepseek_r1.md)、[mla](../modules/mla.md)），K2-Thinking 在此基线之上叠加本页所述的部署优化。溯源：`moonshotai/Kimi-K2-Instruct/config.json`（verified 2026-05-15）+ 随仓自带、复用 DeepseekV3 的 `modeling_deepseek.py`。

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

关键参数（取自 `moonshotai/Kimi-K2-Instruct/config.json`，仅保留对部署有意义的行）：

| 模块 | 参数 | 值 |
|------|------|----|
| — | n_layers | 61 |
| — | hidden | 7168 |
| — | vocab | 163840 |
| — | first_k_dense_replace | 1（仅 layer 1 为 Dense FFN，其余为 MoE） |
| MLA | n_heads | 64 |
| MLA | q_lora_rank | 1536 |
| MLA | kv_lora_rank | 512 |
| MLA | qk_nope_head_dim | 128 |
| MLA | qk_rope_head_dim | 64 |
| MLA | v_head_dim | 128 |
| MoE | n_routed_experts | 384 |
| MoE | n_shared_experts | 1 |
| MoE | top_k | 8 |
| MoE | moe_intermediate | 2048 |
| FFN | intermediate_size（dense 层） | 18432 |

> 上表 `n_heads=64` 与本页「Attention Head 128 → 64」口径一致（K2 系相对 DeepSeek-V3 的 128 精简至 64）。stock checkpoint 自带 FP8 权重为部署无关事实，本页 NPU 部署侧的精度口径（MoE W4A16 / Attention BF16）见模型Guide的量化边界，二者分属不同层面，不构成矛盾。

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/kimi_k2_thinking_deployment.md)：配置、开关、失效条件与回退入口。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/kimi-k2-thinking/kimi_k2_thinking_inference_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/kimi-k2-thinking/kimi_k2_thinking_inference_guide.md)（Highlights、Prefill CP、Decode Attn-DP + MoE-EP + 局部 TP、融合 Kernel、MTP、Future Plan 六个章节）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/kimi-k2-thinking/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/kimi-k2-thinking/README.md)（硬件要求、docker 镜像、拉起流程）；`models/kimi-k2-thinking/config/kimi_k2_thinking_rank_128_128ep_decode_benchmark.yaml` / `kimi_k2_thinking_rank_64_64ep_prefill_benchmark.yaml`（部署规格）；`models/kimi-k2-thinking/runner_deepseek.py`（`DeepSeekRunner` 类，legacy ModelRunner 路径，Kimi 自带副本）；`models/kimi-k2-thinking/models/modeling_deepseek.py`（R1 同款 DeepseekV3 架构的独立适配副本，@2f82d10 实测 2381 行 ≠ R1 `models/deepseek_r1/models/modeling_deepseek.py` 2761 行，非同一文件）

## Links

- [deepseek-r1](deepseek_r1.md)（架构同族；执行器与模型文件分别核对）
- [atlas-a3](../platforms/atlas_a3.md)
- [torchair](../frameworks/torchair.md)
- [ascendc](../frameworks/ascendc.md)
- [mla](../modules/mla.md)
- [mla-prolog](../kernels/mla_prolog.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [context-parallel](../parallelism/context_parallel.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [data-parallel](../parallelism/data_parallel.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [double-routing](../techniques/double_routing.md)
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)
- [zigzag-cp](../parallelism/zigzag_cp.md)
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [moe-multi-stream](../techniques/moe_multi_stream.md)
- [superkernel](../techniques/superkernel.md)
- [weight-nz](../techniques/weight_nz.md)
- [w8a8c8](../quantization/w8a8c8.md)（说明 Kimi-K2-Thinking 不支持 C8）
