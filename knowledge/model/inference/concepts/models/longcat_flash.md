---
type: Concept
title: LongCat-Flash
description: 说明 LongCat-Flash 的 ScMoE 双段结构、MLA 与零计算专家；部署流程、优化差异和来源性能分别由 Guide、规则/案例和观测卡维护。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T13:46:35Z'
platforms:
- a3
---

# LongCat-Flash

## 模型结构与机制边界

LongCat-Flash 是 560B MoE 模型，核心为 ScMoE：每个 Transformer Block 包含 Attention、FFN、第二段 Attention 与 MoE 的双段结构，存在可并行的数据路径。Attention 使用 MLA；MoE 包含路由专家与零计算专家，零计算专家的映射为 `MoE(x)=x`。结构机制分别见[MLA](../modules/mla.md)和[专家路由](../techniques/moe_dispatch_combine_v2.md)。

来源的 NPU 实践面向 Atlas A3、自研 CANN Executor。原始并行策略图仅用于说明计算路径：

![LongCat-Flash 原始 overlap 策略](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/figures/overlap_strategy.png)

## 部署、优化与观测入口

| 要解决的问题 | 维护正文的入口 |
| --- | --- |
| 权重、配置、图缓存、执行与统一验收 | [LongCat A3 部署流程](../../guides/models/longcat_flash_deployment.md) |
| ScMoE 多流与控核取舍 | [多流规则](../../optimizations/rules/decode_multi_stream_overlap_core_balance.md) |
| o_proj 和 dense MLP 的局部 TP | [LongCat TP 案例](../../optimizations/cases/longcat_dp_tp_projections.md) |
| 权重预取的具体排布 | [LongCat 预取案例](../../optimizations/cases/longcat_a3_decode_weight_prefetch.md) |
| GE SuperKernel 的范围与布局 | [LongCat SuperKernel 案例](../../optimizations/cases/longcat_a3_superkernel_layout_fusion.md) |
| Attention/FFN 分离与回退 | [AFD 规则](../../optimizations/rules/afd_attn_ffn_disaggregation.md) |
| 固定负载的自报性能 | [LongCat A3 来源观测](../../optimizations/benchmark_observations/longcat_a3_afd_source_benchmark.md) |

## 当前实现与验证边界

当前主模型与 MTP 使用 InferenceConfig/CommManager 和 ForwardMetaData；KV Cache 由共享管理器绑定到模块，packed-token Prefill 与 Attention-SP 路径负责 token padding/布局恢复。模型级入口统一计算 Prefill MoE chunk 数，避免每层重复 EP 同步。

当前支持 eager、GE、npugraph_ex，但多流不支持 eager、SuperKernel只支持GE，CP仅1，MTP宽度仅0/1/2。AFD采用两半rank配对，npugraph_ex Decode可延迟接收至汇合点。KVP已无配置与实现入口。

结构与API存在不代表已在本次运行验证；吞吐仍需按实际软件、路由与输入复测。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/README.md)（primary）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）
- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（supporting）

## Links

- [longcat-flash-lite](longcat_flash_lite.md)（减配验证模型：包含 MoE、MLA 与 Lite 独立的 N-gram Embedding 模块、缩小层/expert 数，A2/A3 单节点冷启动优化）
- [atlas-a3](../platforms/atlas_a3.md)
- [torchair](../frameworks/torchair.md)
- [ascendc](../frameworks/ascendc.md)
- [mla](../modules/mla.md)
- [mla-prolog](../kernels/mla_prolog.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [data-parallel](../parallelism/data_parallel.md)
- [kvp](../parallelism/kvp.md)
- [afd](../techniques/afd.md)
- [moe-multi-stream](../techniques/moe_multi_stream.md)（LongCat-Flash ScMoE 变体）
- [weight-prefetch](../techniques/weight_prefetch.md)
- [superkernel](../techniques/superkernel.md)
- [double-routing](../techniques/double_routing.md)
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [w8a8c8](../quantization/w8a8c8.md)
- [multi-stream](../techniques/multi_stream.md)（多流编排/控核方法论总纲；LongCat ScMoE 多流+控核+AFD 为代表案例）
