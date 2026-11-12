---
type: Guide
title: Attention 融合链选型：GQA、MLA Absorb 与 Indexer 稀疏路径
description: 按真实注意力结构选择 Norm、RoPE、缓存写入、FIA/稀疏 FA 与输出投影链路，区分 Prefill 和 Decode 的缓存消费者。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/module-attention-gqa.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/module-attention-mla-absorb.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/module-attention-mla-indexer.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/models/modeling_qwen3_moe.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: supporting
created_at: '2026-11-09T09:23:46Z'
updated_at: '2026-11-09T09:23:46Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# Attention 融合链选型：GQA、MLA Absorb 与 Indexer 稀疏路径

## 适用范围与结构判定

这是 Recipes 模型接入任务的链路指南，接口的芯片与版本支持继续核对对应知识卡及实际 API。先判断标准 GQA/MHA、无 Indexer 的 MLA、带 LightningIndexer 的稀疏 MLA，分别选参考，不因模型同属 MoE 就复制注意力路径。

| 结构 | 前处理与缓存 | 注意力与后处理 |
| --- | --- | --- |
| GQA/MHA | residual+RMSNorm、合并 QKV、可选 QK norm、RoPE、按 slot 写 KV | Prefill 可直接读当前 K/V，Decode 读历史 paged cache；FIA 后接 o_proj |
| MLA 无 Indexer | Q/KV 低秩投影，区分 normal 与 absorb；可用 MLAProlog 融合投影、Norm、RoPE 和写缓存 | absorb 的 key/value 共享 latent nope cache，rope 分传；FIA 后做 V 上投影，再 o_proj |
| MLA+Indexer | MLAProlog 与独立 Indexer 投影/RoPE/缓存/TopK | TopK 索引传给稀疏 FA，C8 路径连同 cache scale 使用量化稀疏接口；随后 V absorb 和 o_proj |

Prefill 不是一律展开 K/V，Decode 也不是只换缓存指针：R1 分 normal/absorb/prolog，DSA 的短长 Prefill 还存在不同算路。具体链路由阶段、shape、量化和实现共同决定。优先复用已验证的同结构路径，算子不支持时保留非融合等价实现。

## 替换与正确性检查

核对 npu_add_rms_norm 首层 residual 为空时的退化路径；保持模型特有 QK norm 和 RoPE 编码；显式传实际 Q/KV head 数。缓存的物理页形状与 input_layout 字符串不同，不能凭 TND 字面把 NZ cache reshape 成普通三维张量。MLA latent KV 的共享语义不等于把所有 KV 沿 attn_tp 切分。

对每个边界保存 shape、dtype、scale、普通/累计长度、slot 和 block_table，先比较 eager 输出，再检查图模式及真实 kernel。融合减少调用和中间搬运只是收益机制，没有受控测量时不写通用加速比。精度或能力不匹配时逐模块回退，不能用近似结果换取跑通。

## 按需继续读取

- [FIA 版本、layout 与参数](../../concepts/kernels/fused_infer_attention_score.md)
- [MLA Prolog](../../concepts/kernels/mla_prolog.md)与[长短 Prefill 取舍](../../optimizations/rules/dsa_sparse_prefill_mla_scheme_by_seqlen.md)
- [C8 写入与消费闭环](../../optimizations/rules/mla_c8_int8_kv_cache_op_wiring.md)
- [RoPE 预计算](rotary_embedding_cache_precompute.md)与[FA 精度排查](../../runbooks/precision/precision_kvcache_fa_fusion_pitfalls.md)

## Evidence

- [.agents/skills/model-infer-fusion/references/module-attention-gqa.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/module-attention-gqa.md)
- [.agents/skills/model-infer-fusion/references/module-attention-mla-absorb.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/module-attention-mla-absorb.md)
- [.agents/skills/model-infer-fusion/references/module-attention-mla-indexer.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/module-attention-mla-indexer.md)
- [models/qwen3_moe/models/modeling_qwen3_moe.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/models/modeling_qwen3_moe.py)
- [models/deepseek_r1/models/modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)
