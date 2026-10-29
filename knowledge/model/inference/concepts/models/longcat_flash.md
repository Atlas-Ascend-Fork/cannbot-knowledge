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
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/longcat_flash_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-21T09:02:45Z'
platforms:
- a3
---

# LongCat-Flash

## 模型结构与机制边界

LongCat-Flash 是 560B MoE 模型，核心为 ScMoE：每个 Transformer Block 包含 Attention、FFN、第二段 Attention 与 MoE 的双段结构，存在可并行的数据路径。Attention 使用 MLA；MoE 包含路由专家与零计算专家，零计算专家的映射为 `MoE(x)=x`。结构机制分别见[MLA](../modules/mla.md)和[专家路由](../techniques/moe_dispatch_combine_v2.md)。

来源的 NPU 实践面向 Atlas A3、自研 CANN Executor。原始并行策略图仅用于说明计算路径：

![LongCat-Flash 原始 overlap 策略](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/figures/overlap_strategy.png)

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

## 历史与验证边界

KVP 部署在后续固定版本撤回；历史配置、legacy 代码与入口守卫由[KVP 机制](../parallelism/kvp.md)和[已停用 Guide](../../guides/deployment/kvp_longseq_decode.md)统一说明。本模型卡不把旧配置列为当前可启用规格。

实际部署需要核对具体提交、卡数/并行、精度、后端和输入。结构相似不表示可继承其他模型的配置；本次迁移没有执行模型，也不把来源的自报 benchmark 当作已验证收益。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/longcat-flash/longcat_flash_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/longcat_flash_optimization.md)（11 大章节：通用优化 / 图模式 / 图编译缓存 / 多流并行与控核 / 权重预取 / SuperKernel / MLA 低秩压缩 + o_proj TP / KVP / MoE EP / MLP 合并与 TP / MTP / AFD）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/longcat-flash/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/README.md)（benchmark 表、长序列 OOM 处理、Send/Recv 1:1 约束）；`models/longcat-flash/config/*.yaml`（5 份默认 + 3 份 CI 部署配置）；`models/longcat-flash/models/modeling_longcat_flash.py` / `ffn.py` / `mtp.py`（`LongcatFlashAttention.forward_page_attention_absorb`、MoE forward、`npu_prefetch`、`npu_stream_switch`、`limit_core_num`、`superkernel_scope` 使用处）；`models/longcat-flash/runner_longcat_flash.py`（主 runner）；`models/longcat-flash/utils/convert_model.py`（BF16 → W8A8 权重转换）
- 原始模型：Meituan LongCat-Flash-Chat HF repo（`meituan-longcat/LongCat-Flash-Chat`）；论文 arXiv 2509.01322（四阶段并行策略来源）
- KVP 撤回与遗留代码的来源见 [PR501](https://gitcode.com/cann/cann-recipes-infer/merge_requests/501)、[固定入口守卫](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat-flash/models/model_setting.py)；具体历史机制由 KVP 卡维护。

## Links

- [longcat-flash-lite](longcat_flash_lite.md)（减配验证模型：保留 MoE+MLA+N-gram Embedding 核心结构、缩小层/expert 数，A2/A3 单节点冷启动优化）
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
