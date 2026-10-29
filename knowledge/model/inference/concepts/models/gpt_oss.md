---
type: Concept
title: GPT-OSS
description: GPT-OSS 的 GQA、可学习 attention sink、滑窗与带 bias 的 clamped GLU 专家机制。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/gpt-oss/gpt_oss_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-21T10:02:02Z'
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

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/gpt_oss_deployment.md)：配置、开关、失效条件与回退入口。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/gpt-oss/gpt_oss_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/gpt-oss/gpt_oss_optimization.md)（Attention TP / MoE TP / 固定 KV Cache / 融合算子 / FA / AIV 六大章节）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/gpt_oss/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/gpt_oss/README.md)（Atlas A2 环境准备、权重转换约束、单 batch 限制、在线切分默认开启）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/gpt_oss/config/gpt_oss_{20b,120b_8tp}.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/gpt_oss/config/gpt_oss_20b.yaml)（两份部署模板）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/gpt_oss/models/modeling_gpt_oss.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/gpt_oss/models/modeling_gpt_oss.py)（`GptOssAttention.sinks` 可学习 sink + `learnable_sink` 入参 / `GptOssExperts` clamped-GLU 带 bias / `GptOssAttention` k_cache 占位待 runner 分配 / `GptOssMLP` 参考实现）

## Links

- [atlas-a3](../platforms/atlas_a3.md) — 本样例目标为 Atlas A2，但 cann-recipes-infer 主体面向 A3
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [ascendc](../frameworks/ascendc.md)
