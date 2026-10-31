---
type: Concept
title: Gated DeltaNet (GDN)
description: 当前GDN递推机制、Next自研与Qwen3.5原生差异、两组投影/索引Mamba状态及已删除chunk回退。
tags:
- task.design
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/stage6/0001-support-gdn-cp.patch
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:31:37Z'
platforms:
- a3
---

# Gated DeltaNet (GDN)

## Summary

承担线性复杂度上下文聚合的线性注意力模块，基于 Mamba/DeltaNet 风格的递推状态更新加门控机制。在混合注意力模型（[qwen3-next](../models/qwen3_next.md)、[qwen3-5-moe](../models/qwen3_5_moe.md)）中与 [gated-attention](gated_attention.md) / full attention 交替堆叠。相对标准 Attention，GDN 在长序列下显著降低计算与显存复杂度，但引入 Conv1d 和状态递推，早期部署采用纯TP，序列并行需要额外的卷积边界和递推状态交换。

各模型的 GDN 在概念角色上一致（线性复杂度的线性注意力，DeltaNet 风格 gated 递推 + Conv1d），但在以下三处存在**显式差异**：

- **输入投影**：Qwen3-Next 用独立 `in_proj`；Qwen3.5-MoE当前分为`in_proj_qkvz`与`in_proj_ba`两组投影，旧单一in_proj_fused已撤下（见下方 Variants 与 [qwen3-5-moe](../models/qwen3_5_moe.md) 矩阵融合）。
- **Prefill kernel 选择**：Qwen3-Next 走 PyPTO ChunkGDN；Qwen3.5-MoE 走 torch_npu 原生 `torch_npu.npu_chunk_gated_delta_rule`（当前已删除PyTorch chunk回退）。
- **输出 Norm 变体**：Qwen3-Next 在非 Extend 分支可用 AscendC mambav2_rmsnormgated，Extend 仍 self.norm；Qwen3.5-MoE 用 `Qwen3_5MoeRMSNormGated`（`torch_npu.npu_rms_norm` + 门控相乘）。

本卡部署实现限定于来源所述 Atlas A3 的固定 Qwen3-Next / Qwen3.5-MoE 路径；递推公式是机制层解释，不能由此推定其他芯片或框架已接入这些融合算子。详见下方 Variants。

## Mechanism

```mermaid
flowchart LR
 H[hidden_state] --> InProj[in_proj]
 InProj --> QKV[mix_qkv]
 InProj --> G[g = -exp A_log × softplus a+dt_bias]
 InProj --> BETA[beta = sigmoid(b)]
 QKV --> Conv[Causal Conv1d<br/>高精度, 维护 conv_state]
 Conv --> Norm[L2Norm Q/K]
 Norm --> Delta[Delta Rule 递推<br/>ssm_state 更新]
 G --> Delta
 BETA --> Delta
 Delta --> OutNorm[Output Norm + Gate<br/>RMSNorm + SiLU + Mul]
 OutNorm --> OutProj[out_proj]
 OutProj --> Y[output]

 MambaCache[(mamba_cache<br/>conv_state + ssm_state)]
 Conv <--> MambaCache
 Delta <--> MambaCache
```

- **输入投影**：hidden state 经 in_proj 得到 `mix_qkv`（Q/K/V 混合）、`g`（forget gate）、`beta`（更新门控）。Qwen3.5-MoE当前QKV/Z与B/A分两组投影，各自按TP/量化加载，最终拼出递推所需输入。
- **Causal Conv1d**：在 Sequence 维度做短窗卷积（`kernel_size` 典型值 4）。维护 `conv_state` 作为跨步历史。Decode/MTP 下通过 `torch_causal_conv1d_update_npu` 融合更新 `conv_state`。
- **Gating**：对 Q/K 做 L2 归一化；更新门 beta=sigmoid(b)，对数遗忘因子 g=-exp(A_log)·softplus(a+dt_bias)，递推中取 exp(g) 衰减状态；不能对 g 套 Sigmoid。
- **Delta Rule 状态更新**：维护 SSM 状态矩阵 `ssm_state`，按 DeltaNet 规则递推：
 - 以参考状态 S 的形状 [head, Dk, Dv] 为例，先 S′=exp(g)·S，再 delta=beta·(v−kᵀS′)，最后 S=S′+k⊗delta；融合接口若以 [Dv,Dk] 保存状态需作对应转置；
 - 输出 out=qᵀS（q 的 scale 由具体调用方处理）。
- **状态缓存**：`mamba_cache` 由 `mamba_cache_indices` 索引，每个请求独占一槽；Qwen3-Next 自研 MTP kernel 用 num_accepted_tokens 选择上一轮初始状态槽，本轮依 actual_seq_lengths 处理并保存全部验证 token 状态，不能按 accepted 数过滤本轮写回。
- **输出**：经 `RMSNorm + SiLU + Mul` 门控归一化（mambav2_rmsnormgated），再经 out_proj 输出。

## Variants

- **Prefill 路径（Chunk GDN）**：长序列沿 chunk 做分块并行递推。
 - **Qwen3-Next**：基于 PyPTO 实现的 ChunkGDN 融合 kernel（[pypto](../frameworks/pypto.md)）。
 - **Qwen3.5-MoE**：走 **torch_npu 原生算子 `torch_npu.npu_chunk_gated_delta_rule`**（非 PyPTO），接收 TND 的 Q/K/V、beta、initial_state、actual_seq_lengths、decay 参数 g，调用前由 F.normalize 完成 Q/K 的 L2 归一化，再由 chunk 算子执行对应递推；不能将 L2 步骤归为此调用内部，也不由 API 调用推定其未披露的全部内部实现，输出 `core_attn_out` + `last_recurrent_state`。
- **Decode/MTP 路径（Recurrent GDN）**：单步或少量 draft token 的递推，由 AscendC 融合算子 [recurrent-gated-delta-rule](../kernels/recurrent_gated_delta_rule.md) 一次性完成 Sigmoid+L2Norm+Attn+State 更新。两者共享递推语义，但 Qwen3-Next stage5 调用自研 torch.ops.npu_ops_transformer_ext.recurrent_gated_delta_rule，Qwen3.5-MoE 调 torch_npu.npu_recurrent_gated_delta_rule；后者内部源码未披露，不能认定共用该 AscendC 实现。
- **输出 Norm+Gate**：Qwen3-Next 由 AscendC 融合算子 [mambav2-rmsnormgated](../kernels/mambav2_rmsnormgated.md) 融合 RMSNorm、SiLU、Mul，环境变量 USE_CUSTOM_NORM_KERNEL=true 仅对非 Extend 分支使能，形状/布局限制见算子页；Qwen3.5-MoE 由 `Qwen3_5MoeRMSNormGated`（`torch_npu.npu_rms_norm` + 门控相乘，以 Z 分支作门控输入）完成。
- **W8A8 量化**：Qwen3-Next 除 Conv1d 外的 Linear 层启用 Per-Channel W8 + Per-Token A8，Conv1d 保持高精度；Qwen3.5-MoE新增950 FP8与在线MXFP8，详见模型Guide，不能移植Next整数W8A8配置。

## Qwen3.5 当前状态与算子边界

GDN通过MambaCacheEntry声明conv_state [K-1,conv_dim]与ssm_state [v_heads,Dv,Dk]，均BF16，以block_table[Mamba]的请求槽索引。Prefill更新对应槽，Decode将ssm_state_indices传原生算子，num_accepted_tokens=None；该模型明确next_n=0，不声称已支持MTP。

原生chunk/recurrent调用前均已计算beta.sigmoid、F.normalize(Q/K)和g。Next自研op在kernel内处理的Sigmoid/L2Norm不能直接套给该API。950融合causal conv支持索引状态，其他平台保留卷积适配。

## Performance Characteristics

- 线性复杂度 O(S·d²)，适合长序列；本段描述早期 full-TP GDN 实现；Conv1d 与递推状态使 CP 需额外交换，不能由结构断言 GDN 永远不支持 CP。早期启用 CP（prefill 阶段 Gated Attention 走 CP+TP 混合并行）时，GDN 不参与序列切分，而是回退到完整 TP 组：`use_full_tp = get_context_model_parallel_world_size() > 1`，此时 `tp_world_size = get_tensor_model_parallel_world_size()` 而非 attention 的 CP 子组 size，GDN 仍走纯 TP。CP 的序列切分 / AllGather / ZigZag 负载均衡仅作用于 Gated Attention 路径，见 [qwen3-next](../models/qwen3_next.md)。
- TP 切 num_kv_head 方向，上限由 num_kv_head 数决定（源仅定性说明上限为 num_kv_head，未给出具体数值；gap）。进一步并行需要引入 linear-attention 层的序列并行（当前stage6/ZECO已有专门GDN CP，不能仅按早期TP报告判断，见下条）。
- 后续 stage6 的 GDN CP 通过边界卷积和递推状态传播切分序列，具体单batch、head_dim与TP条件见 [ZECO 案例](../../optimizations/cases/qwen3_next_gdn_context_parallel_zeco.md)。这些实现与早期仅 Gated Attention 做CP的部署分开理解。
- Decode 热点：`conv_state`/`ssm_state` 读写和多个小算子的 Launch 开销；融合后 Launch 数降低、UB 复用。
- MTP 下需保证 `num_accepted_tokens` 正确驱动 state 的回退/前进，否则下一轮状态错。

## Evidence

- [qwen3_next_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md)（primary）
- [modeling_qwen3_5_moe.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py)（implementation）
- [recurrent_gated_delta_rule.h](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h)（implementation）
- [0001-support-gdn-cp.patch](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/stage6/0001-support-gdn-cp.patch)（implementation）

## Links

- [qwen3-next](../models/qwen3_next.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [gated-attention](gated_attention.md)
- [recurrent-gated-delta-rule](../kernels/recurrent_gated_delta_rule.md)
- [mambav2-rmsnormgated](../kernels/mambav2_rmsnormgated.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [ascendc](../frameworks/ascendc.md)
- [pypto](../frameworks/pypto.md)
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [deltanet-pretrain](../../../training/guides/recipes/deltanet_pretrain.md)（跨域·训练：训练侧 DeltaNet(Delta Rule)样例,推理侧为 Gated DeltaNet）
- [gdn-chunk-kernels](../../../training/concepts/kernels/gdn_chunk_kernels.md)（跨域·训练：GDN chunk-parallel 训练算子族，Prefill ChunkGDN 语义在 MindSpeed Triton 上的前/反向实现）
- [gated-deltanet-train](../../../training/concepts/modules/gated_deltanet_train.md)（训练侧 GDN 部署：chunk/Flash 后端 + GDN 上下文并行）
