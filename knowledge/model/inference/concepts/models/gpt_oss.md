---
type: Concept
title: GPT-OSS
description: 当前GPT-OSS的sink/滑窗与clamped GLU、packed/Page cache和独立TP组；部署以BF16、batch1/eager示例验收。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/models/modeling_gpt_oss.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/gpt-oss/gpt_oss_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:23:20Z'
platforms:
- a2
---

# GPT-OSS

## Summary

GPT-OSS包含20B/120B规格，使用GQA、可学习attention sink和路由MoE；专家带bias，激活为clamped GLU，不等于普通SwiGLU。

本卡保留模型结构，A2样例的权重转换、batch/eager/TP限制由部署Guide维护。平台配置、开关和验收步骤见[模型部署流程](../../guides/models/gpt_oss_deployment.md)，此处只保留模型机制。

## Architecture And Serving Traits

```mermaid
flowchart TD
 In[Hidden] --> RN1[RMSNorm]
 RN1 --> MQKV[qkv_proj<br/>合并 Q/K/V 一次 matmul]
 MQKV --> Split[Split → Q/K/V]
 Split --> FA[npu_fused_infer_attention_score_v2]
 FA --> OP[o_proj 行切]
 OP --> Add1[+ residual]
 Add1 --> RN2[AddRMSNorm]
 RN2 --> Router[router<br/>npu_moe_gating_top_k_softmax]
 Router --> Routing[npu_moe_init_routing<br/>+ compute_expert_tokens]
 Routing --> GMM[npu_grouped_matmul<br/>gate_up_proj+bias → clamped-GLU<br/>limit=7.0,alpha=1.702,(up+1)*glu → down_proj+bias]
 GMM --> Fin[npu_moe_finalize_routing]
 Fin --> Add2[+ residual]
 Add2 --> Out[Hidden']
```

- **Softmax Attention + GQA + 可学习 attention sink**：QKV 头数通过 HuggingFace `configuration_gpt_oss.py` 配置决定，支持 MQA/GQA（`num_key_value_heads <= num_heads`）。每个 attention 头额外持有一个可学习 sink 标量 `self.sinks = nn.Parameter(empty(num_attention_heads_per_rank))`，作为 `learnable_sink` 入参传给 `npu_fused_infer_attention_score_v2`，相当于在 softmax 分母里挂一个常驻的"无 token"通道；该参数按 rank 切分（`load_weights` 里 `"sinks" in name` 分支按 `head_start / heads_per_rank` narrow）。attention sink 是 GPT-OSS 的标志性设计，并非裸 softmax attention。
- **MoE**：routed experts，无 shared expert。逻辑上是 gate / up / down 三矩阵，但物理实现已将 gate 与 up 合并为单个 `gate_up_proj`（带 bias），与 `down_proj`（带 bias）共两个 GMM；激活为带 clamp 的 GLU 变体而非裸 SwiGLU，详见下文。
- **支持滑窗注意力**：`config.layer_types[layer_idx] == "sliding_attention"` 的层走 `sliding_window`，对应 FIA 的 `sparse_mode=4`；非滑窗层 `sparse_mode=3`。属仓内带 attention-sink + 滑窗的非裸 MoE LLM 结构。

## 当前缓存与通信接入

模型已迁移packed token、1D position_ids及统一Page cache。FullAttention与SlidingWindow的CacheEntry按层声明dtype、head、block_size与窗口，由get_cache_info交给共享管理器，旧runner自管连续KV说明失效。Prefill切除padding直接计算有效K/V后写入；Decode先scatter_nd更新，再以该attention类型的block_table与block_size读取PA，learnable_sink仍保留。

TP现在分别使用CommManager的Attention/MoE/LMHead组；sink加载按Attention rank，专家权重与bias按MoE rank，不能用一个全局rank代替所有组。当前样例仍保持三种TP相同、batch1/eager，不从分组改造推导EP或图模式已验证。

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/gpt_oss_deployment.md)：配置、开关、失效条件与回退入口。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/README.md)（primary）
- [modeling_gpt_oss.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/models/modeling_gpt_oss.py)（implementation）
- [gpt_oss_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/gpt-oss/gpt_oss_optimization.md)（supporting）

## Links

- [atlas-a3](../platforms/atlas_a3.md) — 本样例目标为 Atlas A2，但 cann-recipes-infer 主体面向 A3
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [ascendc](../frameworks/ascendc.md)
