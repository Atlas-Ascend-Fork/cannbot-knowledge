---
type: Concept
title: HSTU
description: HSTU 生成式推荐的离散 ID、jagged 序列、稀疏 Embedding 容量与推荐缓存机制。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.kv_cache
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hstu/hstu_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hstu/modules/paged_hstu_infer_layer.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:19:33Z'
platforms:
- a2
---

# HSTU

## Summary

HSTU（Hierarchical Sequential Transduction Unit）面向生成式推荐，将用户、物品与上下文的离散ID序列用于检索和排序。其容量侧重稀疏Embedding，序列使用jagged形态，不能照搬文本LLM的词表、KV与并行假设。

原总览引用的论文业务A/B数字没有本NPU样例的对应实验，不作为本卡部署收益。平台配置、开关和验收步骤见[模型部署流程](../../guides/models/hstu_deployment.md)，此处只保留模型机制。

## Architecture And Serving Traits

HSTU 是生成式推荐模型，与 LLM 的核心差异：

| 维度 | LLM | HSTU (GR) |
| ---- | ---- | ---- |
| 输入 | 文本 token 序列（固定词表） | 用户/物品/上下文的离散 ID 序列（千万~亿级词表） |
| 容量主体 | dense Transformer 权重 | 稀疏 **Embedding Tables** |
| 序列形态 | padded / packed token 序列 | **jagged tensor**（变长，含 `seqlen_offsets` / `num_candidates_offsets`） |
| 并行侧重 | TP + EP + DP | **Embedding TP + DP** |
| KV Cache | Paged Attention KV | Paged HSTU KV + 多级缓存（device + Host Offload） |
| 任务 | 自回归 token 生成 | 检索 + 排序（ranking）一体 |

```mermaid
flowchart TD
 In[ID 序列 + positional + timestamp] --> Emb[Embedding TP Lookup]
 Emb --> Jag[Jagged Tensor 组装]
 Jag --> HSTUBlock[HSTU Block × L]
 HSTUBlock --> InProj[input LayerNorm + in_linear_silu]
 InProj --> Q[U/V/Q/K jagged]
 Q -->|先 append_kvcache| Reshape
 Q --> FA[hstu_paged 融合算子<br/>含 silu_scale + paged KV + target_group]
 FA --> MLP[输出归一化 + U 门控<br/>输出投影 + 残差]
 MLP --> Post[Ranking 输出]

 subgraph KV 管理
 Kcache[paged_k_cache / paged_v_cache<br/>layout: &#91;L,2,pages,block&#93;]
 Reshape[_npu_reshape_and_cache<br/>append_kv_cache]
 Offload[KV Offload Stream<br/>异步到 Host]
 end
 Reshape --> Kcache
 Kcache -->|append 完成后读取| FA
 Kcache -.->|每层 Attention 完成即触发| Offload
```

## 部署与证据入口

- [模型部署与验收流程](../../guides/models/hstu_deployment.md)：配置、开关、失效条件与回退入口。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md)（primary）
- [hstu_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hstu/hstu_optimization.md)（supporting）
- [paged_hstu_infer_layer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hstu/modules/paged_hstu_infer_layer.py)（implementation）

## Links

- [embedding-tp](../parallelism/embedding_tp.md)
- [data-parallel](../parallelism/data_parallel.md)
- [kvcache-offload](../techniques/kvcache_offload.md)（HSTU 变体）
- [ascendc](../frameworks/ascendc.md)
