---
type: Concept
title: recurrent_gated_delta_rule
description: Next自研GDN递推kernel与当前Qwen3.5原生API的输入/状态边界，后者只支持非投机Decode。
tags:
- task.implementation
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/recurrent_gated_delta_rule/recurrent_gated_delta_rule.cpp
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py
  role: constraint
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:31:37Z'
platforms:
- a3
---

# recurrent_gated_delta_rule

## Summary

Decode/MTP 阶段 [gated-deltanet](../modules/gated_deltanet.md) 的融合算子，用于混合注意力模型（[qwen3-next](../models/qwen3_next.md)、[qwen3-5-moe](../models/qwen3_5_moe.md)）线性注意力层的单步/少量 draft token 递推。一次 kernel launch 完成 Sigmoid + L2Norm + Gated Delta 递推注意力 + `ssm_state` 选择性更新，消除 Decode GDN 路径多个小算子的 Launch 和中间搬运开销。BF16 输入输出、FP32 累加，AIV 单元执行（`KERNEL_TYPE_AIV_ONLY`）。

本页正文（Role In Pipeline / Performance Signals / Optimization Notes）记录的是 **Qwen3-Next 自研 AscendC 实现**的内部细节（`recurrent_gated_delta_rule.cpp` / `op_kernel/*.h`，经 `torch.ops.npu_ops_transformer_ext.recurrent_gated_delta_rule` 调用）。Qwen3.5-MoE 仅在 `_forward_decode` 中通过 **`torch_npu.npu_recurrent_gated_delta_rule` 原生 API** 调用同名语义的算子，源未披露其 AscendC 内部实现——两者使用同一算子语义，但不应假定共享同一份 AscendC 源码（详见下方 Per-Model Usage）。

## Role In Pipeline

算子内部计算流程（Sigmoid → L2Norm → Gated Delta 递推 → 选择性 state 写回）源图如下：

![recurrent_gated_delta_rule 计算流程](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/figures/rgdr.png)
*来源：[`docs/models/qwen3-next/figures/rgdr.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/figures/rgdr.png)（cann-recipes-infer @ 944d2d3）*

- 位置：Qwen3-Next 每层 GDN 的 Decode 路径末端，替换原 `fused_recurrent_gated_delta_rule_update` Triton/Python 实现。
- 输入：`mix_qkv`（B,S,D，D = 2·nk·dk + nv·dv）、`state`（N,nv,dv,dk）、`beta`（B,S,nv）、可选 `g`/`gk`（forget gate）、`actual_seq_lengths`、`ssm_state_indices`、可选 `num_accepted_tokens`、`scale`。
- 输出：`out`（B,S,nv,dv）+ 原地更新的 `stateOut`（复用 `state` 显存）。
- 在 MTP 路径下，num_accepted_tokens 用于选择上一轮已接受的初始状态槽位（ssm_state_indices[seq0 + accepted - 1]）；本轮递推区间由 actual_seq_lengths 决定，每个被处理的验证 token 均按 ssm_state_indices 保存中间状态。它不按接受数过滤本轮写回，MAX_MTP=8 是实现容量边界。
- 由 Python 侧 `torch.ops.npu_ops_transformer_ext.recurrent_gated_delta_rule` 调用，Meta 函数做形状校验（`d == 2*nk*dk + nv*dv`、`state[1]==nv` 等）。

## Performance Signals

- Tiling 关键参数 `vStep`：按 UB 剩余字节数和 `(dk, dv, nv, MAX_MTP)` 动态计算 `vStep = (ubSize - usedUbBytes) / coeff / 8 * 8`，`vStep >= 8` 否则报错 "shape is too big"。
- UB 预算：MAX_MTP·(4·aDk + 2·aDv) + MAX_MTP·6·aNv + 128B 保留，随后还累加 MAX_MTP·(8·aDk + 4·aDv + 4·aNv)；vStep 必须使用最终累加的 usedUbBytes，不能用中途 ubRestBytes 高估剩余容量。
- 单 buffer 流水（`BUFFER_NUM = 1`）但对 Q/K 队列显式双份（2x inQSize），kv 队列双缓冲；`Brcb` 广播 rstd，`PipeBarrier<PIPE_V>` 分段同步。
- 计算 lane 宽度：`BLK_SIZE = VEC_FLOAT = 64`（FP32 256B vector），对齐到 16（BF16）/8（FP32）。
- `coreNum = GetCoreNum`，按 batch·head（B·NV）粒度分核（`ComputeAvgload()`：`avgload = Ceil(B·NV, blockNum)`，`totalWorkload = B·NV`，`workIdx` 映射 `batchIdx = workIdx / NV`、`headIdx = workIdx % NV`）；每个核内对该 head 的 seq token 由 `ProcessHead` 中 `for (seq_i = seq0; seq_i < seq1; seq_i++)` 串行递推。MAX_MTP=8 决定了单批次最多同时处理 8 个 draft token（MTP1 实际用 2）。

## Per-Model Usage

| 模型 | 实现来源 | 调用入口 | 内部细节是否本页可见 |
| ---- | ---- | ---- | ---- |
| [qwen3-next](../models/qwen3_next.md) | 自研 AscendC kernel（`recurrent_gated_delta_rule.cpp` + `op_kernel/*.h`） | stage5 patch 起 `torch.ops.npu_ops_transformer_ext.recurrent_gated_delta_rule`（stage3 patch 走 `torch_npu.npu_recurrent_gated_delta_rule` 原生 API），`ENABLE_ASCENDC_FUSION_GDN="true"` 使能 | 是（Role In Pipeline / Performance Signals / Optimization Notes 即其细节） |
| [qwen3-5-moe](../models/qwen3_5_moe.md) | torch_npu 原生 API（`Qwen3_5MoeGatedDeltaNet._forward_decode`） | `torch_npu.npu_recurrent_gated_delta_rule` | 否（源未披露 Qwen3.5 的 AscendC 内部实现） |

两者承担Gated Delta递推，但当前Qwen3.5只支持next_n=0；它在原生API调用前已sigmoid(beta)与F.normalize(Q/K)，不将这些步骤重复归入该kernel，但 Qwen3-Next 走仓库自研 AscendC 算子、Qwen3.5-MoE 走 torch_npu 原生封装，**不应假定共享同一份 AscendC 源码**。下文内部细节仅适用于 Qwen3-Next 路径。

## Qwen3.5 当前调用边界

原生调用按block_table[Mamba][:,0]选择ssm_state_indices，直接使用共享ssm_state_cache，num_accepted_tokens=None；Q/K/V转BF16、beta已sigmoid、g为FP32、Q/K已L2归一化。不能复制Next自研mix_qkv/accepted-state接口，更不能由算子名推导Qwen3.5已启用MTP。

## Optimization Notes

- 融合了原 Python 路径中的门控、L2Norm(q,k)、`q·state`、`state·(1-β·kᵀk) + β·kᵀv`、gather/scatter 写回 ssm_state 等步骤；Launch 数由 ~N 降到 1。
- 门控机制（区别于普通 deltanet 的「gated」语义来源）：forget gate `g` 经 `Exp` 得衰减因子 `gama`，对 state 做 `state·=exp(g)`（`Compute()`：`Muls(stateInUb, stateInUb, gama_, ...)`，`gama_` 取自 `CopyInGamaBeta()` 内 `if(hasGama_){ Exp(gamaLocal, ...) }`）；`beta` 经 `Sigmoid`（`Sigmoid<float,false>(betaInUb, ...)`）；q/k 的 L2Norm 用 `Adds(..., 1e-6f, ...)` 后 `Rsqrt`（eps=1e-6）；q 额外乘 `scale`（`Muls(qInUb, qInUb, scale_, ...)`，scale = 1/√dk 由 Python 传入）。
- Q/K/V 共享 `mix_qkv` 连续布局，`tokenStrideSize_ = (2·NK·dk + NV·dv)·sizeof(inType)` 直接按 token 步进，减少 DMA 次数。
- ssm_state_indices 定位各验证 token 的状态保存槽位，num_accepted_tokens 选择上一轮初始状态；这将状态索引/保存融合到 kernel 内，调用方仍须正确管理跨轮接受状态，不能把本轮所有写回等同于已经接受。
- 状态矩阵 `stateOut` 直接复用 `state` 存储（in-place），节省 HBM 写回带宽。
- 使能方式：环境变量 `ENABLE_ASCENDC_FUSION_GDN="true"`。
- MTP 与 C8 互斥（README 约束 3）：当前融合算子在 C8 KVCache 路径未打通。

## Evidence

- [recurrent_gated_delta_rule.cpp](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/recurrent_gated_delta_rule/recurrent_gated_delta_rule.cpp)（primary）
- [recurrent_gated_delta_rule.h](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h)（implementation）
- [modeling_qwen3_5_moe.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py)（constraint）

## Links

- [qwen3-next](../models/qwen3_next.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [gated-deltanet](../modules/gated_deltanet.md)
- [mambav2-rmsnormgated](mambav2_rmsnormgated.md)
- [ascendc](../frameworks/ascendc.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [qwen3-rl](../../../training/guides/recipes/qwen3_rl.md)（跨域·训练：长序列 RL 显存瓶颈分析中，Qwen-Next gated delta rule 被列为「KV Cache 不随序列长度线性增长」的后续模型迭代方向）
- [gdn-chunk-kernels](../../../training/concepts/kernels/gdn_chunk_kernels.md)（跨域·训练：同一 gated delta-rule 的 chunk-parallel 训练算子族，与本页 decode 逐 token recurrent 形式互为时间分解）
- [gated-deltanet-train](../../../training/concepts/modules/gated_deltanet_train.md)（训练侧 GDN：chunk 并行形式与本递归形式互为时间分解）
