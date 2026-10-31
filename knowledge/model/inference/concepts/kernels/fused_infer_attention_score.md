---
type: Concept
title: npu_fused_infer_attention_score (v1 / v2)
description: 核对当前 R1 FIA v1/v2、packed Query 与 Paged NZ KV、C8 反量化参数及框架 block_table 传入。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.precision
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:24:38Z'
platforms:
- a2
- a3
---

# npu_fused_infer_attention_score (v1 / v2)

## Summary

昇腾推理侧的通用 FlashAttention 融合算子（简称 **FIA**），覆盖 Softmax-Attention 的主体计算：`softmax(QKᵀ/√d)·V`，支持 Paged KVCache、Block-Table、分离的 NoPE/RoPE Query/Key 输入、以及 Query / Key / Value 三端的动态 Int8 反量化（dequant_scale_*）。在 DeepSeek-R1 decode 路径中作为 [mla-prolog](mla_prolog.md) 之后的主 FA 算子。

本卡比较固定模型实践的 v1/v2 调用，不据调用差异推定版本新增能力：R1 v1 normal 已分离 query_rope/key_rope，Kimi-K2-Thinking v1 也使用 TND_NTD 与分离 RoPE；R1 v2 吸收/Prolog 路径则采用 Paged NZ KV 与对应量化参数。

## Role In Pipeline

```mermaid
flowchart LR
 MLA[npu_mla_prolog_v3] --> Q[q_nope, q_pe,<br/>dequant_scale_q_nope]
 MLA --> KV[nope_cache NZ<br/>rope_cache NZ]
 Q --> FIA[npu_fused_infer_attention_score_v2]
 KV --> FIA
 AM[atten_mask<br/>sparse_mode 3 in MTP] --> FIA
 AS[actual_seq_lengths_kv<br/>actual_seq_lengths_q] --> FIA
 BT[block_table] --> FIA
 FIA --> O[attn_output N,B*S,D]
 O --> TBMM[npu_transpose_batchmatmul<br/>× kv_b_proj_w_v]
 TBMM --> OP[o_proj]
```

## Key Parameters

Atlas A3 上固定 DeepSeek-R1 Decode 路径 launch（源 `models/deepseek_r1/models/modeling_deepseek.py:L1271`）：

```python
attn_output, _ = self.fa_ops.npu_fused_infer_attention_score_v2(
 q_nope, k_nope, k_nope, # Q_NoPE, K_NoPE, V (MLA 下 K 与 V 共用 nope_cache)
 query_rope=q_pe, key_rope=k_rope, # NoPE/RoPE 分离
 atten_mask=attention_mask,
 actual_seq_kvlen=actual_seq_lengths_kv,
 actual_seq_qlen=actual_seq_lengths_q,
 block_table=block_table,
 dequant_scale_query=dequant_scale_query, # 来自 mla_prolog
 dequant_scale_key=self.ckv_scale if self.kv_cache_quant_mode == "int8" else None,
 dequant_scale_value=self.ckv_scale if self.kv_cache_quant_mode == "int8" else None,
 num_query_heads=self.num_heads_per_rank,
 num_key_value_heads=self.num_key_value_heads_per_rank,
 softmax_scale=self.softmax_scale,
 input_layout="TND_NTD",
 sparse_mode=sparse_mode, # 0: 普通; 3: MTP 因果
 block_size=self.block_size,
 query_quant_mode=3 if self.kv_cache_quant_mode == "int8" else 0,
 key_quant_mode=0, value_quant_mode=0,
)
```

### Query、KV 存储与输出布局

布局字符串不能把后缀直接解释为 K/V 物理存储格式。固定 R1 normal 的 NTD_TND 路径：Query 输入 [N,T,D]，展开后的 K/V 也为 [N,T,D]，输出为 [T,N,D]。本页 R1 v2 Decode 的 TND_NTD 路径：Query 输入 [T,N,D]，输出 [N,T,D]；K/V 是五维 Paged NZ cache，由 block_table / block_size 寻址，不是三维 NTD。INT8 打包维度另见下文 NZ view。

Atlas A3 R1 Prefill 优化文档报告其 NTD 输入、TND 输出方案相对 TND 方案计算效率约提升 15%；这是特定 Prefill 实现的来源观测，不是本页 v2 Decode TND_NTD 的对比实验，也不能据此归因到 Kᵀ 访问连续性。Qwen 的支持产品范围为 A2/A3，不能把 R1 的测量外推到所有 FIA 调用。

### sparse_mode

- `0`：普通因果（decode 单 token 时 `attention_mask = None`）；
- `3`：MTP 场景下 `q_len > 1`，使用 MTP 因果 mask，让多 draft token 之间严格因果 + 对历史全可见。

### 量化入口

- `dequant_scale_query`：来自 `npu_mla_prolog_v3` 的 `dequant_scale_q_nope`，当 W8 + C8 双启时不为 None；
- `dequant_scale_key` / `dequant_scale_value`：`ckv_scale`（KV per-tensor scale，FP32 / torch.float）；
- `query_quant_mode=3`：per-token-head，与 mla_prolog 端 `query_quant_mode=1` 对齐的 C8 路径。

## 当前 packed 与缓存边界

R1 当前按总 token 数推导 q_len，CacheEntry 绑定 nope/rope cache 后按 block_table 参数寻址，不使用旧 self.block_table 的固定请求状态。dequant_scale_q_nope 在 C8 时展成 [T,-1]；输出经 transpose_batchmatmul 与 o_proj 还原 [T,H]。C8 的 NZ factor=2 与 BF16 rope 分开，不能把 query 输出布局当 KV 物理布局。

## Performance Signals

- 是 Decode TPOT 的主要计算组成（MLA 路径下与 mla_prolog、MoE 融合算子并列）。
- Atlas A3 R1 Prefill 的 NTD 方案有约 15% 来源观测，条件和布局见上文；没有本页 v2 Decode 对应的受控收益证据。
- Paged KVCache + block_table 支持大上下文，与 `enable_pa: True`、`pa_block_size: 128` 配合。
- 量化路径下 **Q-side dequant 被内嵌**，该融合不取消 MLAProlog 调用前对 hidden_states 的外部 npu_dynamic_quant，需区分输入激活量化与内部 Query 处理。

## Optimization Notes

- **K/V 共用 nope_cache** 是 MLA 的特性（不是 FIA 限制）：`k_nope` 既作为 K 也作为 V，RoPE 走 `key_rope` 独立通道。
- **NZ view 适配**：在 `kv_cache_quant_mode == "int8"` 时，`factor=2` 打包 int8 后需重新 view，`KV_CACHE_NZ_DIM=16` 硬编码避免高版本 torch 的 dynamic shape 问题。
- 与 `npu_transpose_batchmatmul(attn_output, kv_b_proj_w_v)` 串联实现 V-side up projection；Attention 的 `v_head_dim` 独立于 Q/K 的 `head_dim`。
- v1（`npu_fused_infer_attention_score`）在 `forward_page_attention_normal` 分支使用，布局为 NTD_TND、该调用没有启用 C8（antiquant_scale=None，无 dequant_scale_*），不据此推断 v1 API 的全部能力边界。

## Evidence

- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py)（implementation）
- [deepseek_r1_prefill_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md)（implementation）

## Links

- [deepseek-r1](../models/deepseek_r1.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [qwen-dense](../models/qwen_dense.md)（Qwen2/Qwen3 Dense 用 `npu_fused_infer_attention_score_v2` 全量 + 增量）
- [gemma4-26b-a4b](../models/gemma4_26b_a4b.md)（FIA v1 BSH，`scale=1.0`；sliding 层 prefill/decode 均 `sparse_mode=4`+`pre_tokens=window`；full 层 prefill `sparse_mode=3`、decode `sparse_mode=0`（`pre_tokens=INT32_MAX`））
- [hy3-preview](../models/hy3_preview.md)（FIA v1 BSH GQA，`scale=scale_fa`；prefill `sparse_mode=3`+causal mask、decode `sparse_mode=0`+atten_mask=None）
- [mla](../modules/mla.md)
- [mla-prolog](mla_prolog.md)
- [w8a8c8](../quantization/w8a8c8.md)
- [kv-cache-manager](../frameworks/kv_cache_manager.md)
- [sparse-attn-sharedkv](sparse_attn_sharedkv.md)（并列：通用 FIA 服务 R1/Qwen 的稠密 Softmax-Attention；SAS 是 DeepSeek-V4 的 Shared-KV 统一稀疏/压缩/滑窗 Attention 算子）
- [vggt](../../../spatial/concepts/models/vggt.md) / [hunyuan3d](../../../spatial/concepts/models/hunyuan3d.md)（跨域·空间智能：VGGT global attention 与 Hunyuan3D DiT 用 FIA 替换原生 attention 以入图）
- 跨域·具身：[cosmos-transfer2.5](../../../embodied/concepts/world_models/cosmos_transfer2_5.md)、[cosmos-predict2.5](../../../embodied/concepts/world_models/cosmos_predict2_5.md)、[pi0](../../../embodied/concepts/manipulation/pi0.md)、[isaac-gr00t](../../../embodied/concepts/manipulation/isaac_gr00t.md)、[pi05](../../../embodied/concepts/manipulation/pi05.md)、[alpamayo-r1](../../../embodied/concepts/navigation/alpamayo_r1.md)、[gradient-checkpoint-refine](../../../embodied/concepts/techniques/gradient_checkpoint_refine.md)、[om-atc-offline](../../../embodied/concepts/techniques/om_atc_offline.md)、[flow-matching-action-expert](../../../embodied/concepts/modules/flow_matching_action_expert.md)（VLA / 世界模型用 FIA 替换原生 attention 入图）
