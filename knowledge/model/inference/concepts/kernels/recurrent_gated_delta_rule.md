---
type: Concept
title: recurrent_gated_delta_rule
description: Decode/MTP 阶段 Gated DeltaNet 的融合算子，用于混合注意力模型（Qwen3-Next、Qwen3.5-MoE）线性注意力层的单步/少量 draft token 递推。一次 kernel launch 完成 Sigmoid + L2Norm + Gated Delta 递推注意力 + ssm_state 选择性更新，消除 Decode GDN 路径多个小算子的 Launch 和中间搬运开销。BF16 输入输出、FP32 累加，AIV 单元执行。Qwen3-Next 通过 AscendC 自研算子使用；Qwen3.5-MoE 通过 torch_npu.npu_recurrent_gated_delta_rule 调用同名算子。
tags:
- task.implementation
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/qwen3-next/ops/gated_delta_net/recurrent_gated_delta_rule/recurrent_gated_delta_rule.cpp
  role: primary
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a3
---

# recurrent_gated_delta_rule

## Summary

Decode/MTP 阶段 [gated-deltanet](../modules/gated_deltanet.md) 的融合算子，用于混合注意力模型（[qwen3-next](../models/qwen3_next.md)、[qwen3-5-moe](../models/qwen3_5_moe.md)）线性注意力层的单步/少量 draft token 递推。一次 kernel launch 完成 Sigmoid + L2Norm + Gated Delta 递推注意力 + `ssm_state` 选择性更新，消除 Decode GDN 路径多个小算子的 Launch 和中间搬运开销。BF16 输入输出、FP32 累加，AIV 单元执行（`KERNEL_TYPE_AIV_ONLY`）。

本页正文（Role In Pipeline / Performance Signals / Optimization Notes）记录的是 **Qwen3-Next 自研 AscendC 实现**的内部细节（`recurrent_gated_delta_rule.cpp` / `op_kernel/*.h`，经 `torch.ops.npu_ops_transformer_ext.recurrent_gated_delta_rule` 调用）。Qwen3.5-MoE 仅在 `_forward_decode` 中通过 **`torch_npu.npu_recurrent_gated_delta_rule` 原生 API** 调用同名语义的算子，源未披露其 AscendC 内部实现——两者使用同一算子语义，但不应假定共享同一份 AscendC 源码（详见下方 Per-Model Usage）。

## Role In Pipeline

算子内部计算流程（Sigmoid → L2Norm → Gated Delta 递推 → 选择性 state 写回）源图如下：

![recurrent_gated_delta_rule 计算流程](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/qwen3-next/figures/rgdr.png)
*来源：[`docs/models/qwen3-next/figures/rgdr.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/qwen3-next/figures/rgdr.png)（cann-recipes-infer @ 2f82d10）*

- 位置：Qwen3-Next 每层 GDN 的 Decode 路径末端，替换原 `fused_recurrent_gated_delta_rule_update` Triton/Python 实现。
- 输入：`mix_qkv`（B,S,D，D = 2·nk·dk + nv·dv）、`state`（N,nv,dv,dk）、`beta`（B,S,nv）、可选 `g`/`gk`（forget gate）、`actual_seq_lengths`、`ssm_state_indices`、可选 `num_accepted_tokens`、`scale`。
- 输出：`out`（B,S,nv,dv）+ 原地更新的 `stateOut`（复用 `state` 显存）。
- 在 MTP 路径下根据 `num_accepted_tokens` 决定每个 batch 实际推进的 MTP step 数（最多 MAX_MTP=8），仅把被接受的 token 对应的中间状态写回 `ssm_state`。
- 由 Python 侧 `torch.ops.npu_ops_transformer_ext.recurrent_gated_delta_rule` 调用，Meta 函数做形状校验（`d == 2*nk*dk + nv*dv`、`state[1]==nv` 等）。

## Performance Signals

- Tiling 关键参数 `vStep`：按 UB 剩余字节数和 `(dk, dv, nv, MAX_MTP)` 动态计算 `vStep = (ubSize - usedUbBytes) / coeff / 8 * 8`，`vStep >= 8` 否则报错 "shape is too big"。
- UB 预算：`MAX_MTP · (4·aDk + 2·aDv)` + 额外 `MAX_MTP · 6·aNv` + 128B 保留；剩余容量划分给 Q/K/V/State/Gate 队列。
- 单 buffer 流水（`BUFFER_NUM = 1`）但对 Q/K 队列显式双份（2x inQSize），kv 队列双缓冲；`Brcb` 广播 rstd，`PipeBarrier<PIPE_V>` 分段同步。
- 计算 lane 宽度：`BLK_SIZE = VEC_FLOAT = 64`（FP32 256B vector），对齐到 16（BF16）/8（FP32）。
- `coreNum = GetCoreNum`，按 batch·head（B·NV）粒度分核（`ComputeAvgload()`：`avgload = Ceil(B·NV, blockNum)`，`totalWorkload = B·NV`，`workIdx` 映射 `batchIdx = workIdx / NV`、`headIdx = workIdx % NV`）；每个核内对该 head 的 seq token 由 `ProcessHead` 中 `for (seq_i = seq0; seq_i < seq1; seq_i++)` 串行递推。MAX_MTP=8 决定了单批次最多同时处理 8 个 draft token（MTP1 实际用 2）。

## Per-Model Usage

| 模型 | 实现来源 | 调用入口 | 内部细节是否本页可见 |
| ---- | ---- | ---- | ---- |
| [qwen3-next](../models/qwen3_next.md) | 自研 AscendC kernel（`recurrent_gated_delta_rule.cpp` + `op_kernel/*.h`） | stage5 patch 起 `torch.ops.npu_ops_transformer_ext.recurrent_gated_delta_rule`（stage3 patch 走 `torch_npu.npu_recurrent_gated_delta_rule` 原生 API），`ENABLE_ASCENDC_FUSION_GDN="true"` 使能 | 是（Role In Pipeline / Performance Signals / Optimization Notes 即其细节） |
| [qwen3-5-moe](../models/qwen3_5_moe.md) | torch_npu 原生 API（`Qwen3_5MoeGatedDeltaNet._forward_decode`） | `torch_npu.npu_recurrent_gated_delta_rule` | 否（源未披露 Qwen3.5 的 AscendC 内部实现） |

两者在 Decode/MTP 下完成同一算子语义（Sigmoid + L2Norm + Gated Delta 递推 + `ssm_state` 选择性更新），但 Qwen3-Next 走仓库自研 AscendC 算子、Qwen3.5-MoE 走 torch_npu 原生封装，**不应假定共享同一份 AscendC 源码**。下文内部细节仅适用于 Qwen3-Next 路径。

## Optimization Notes

- 融合了原 Python 路径中的门控、L2Norm(q,k)、`q·state`、`state·(1-β·kᵀk) + β·kᵀv`、gather/scatter 写回 ssm_state 等步骤；Launch 数由 ~N 降到 1。
- 门控机制（区别于普通 deltanet 的「gated」语义来源）：forget gate `g` 经 `Exp` 得衰减因子 `gama`，对 state 做 `state·=exp(g)`（`Compute()`：`Muls(stateInUb, stateInUb, gama_, ...)`，`gama_` 取自 `CopyInGamaBeta()` 内 `if(hasGama_){ Exp(gamaLocal, ...) }`）；`beta` 经 `Sigmoid`（`Sigmoid<float,false>(betaInUb, ...)`）；q/k 的 L2Norm 用 `Adds(..., 1e-6f, ...)` 后 `Rsqrt`（eps=1e-6）；q 额外乘 `scale`（`Muls(qInUb, qInUb, scale_, ...)`，scale = 1/√dk 由 Python 传入）。
- Q/K/V 共享 `mix_qkv` 连续布局，`tokenStrideSize_ = (2·NK·dk + NV·dv)·sizeof(inType)` 直接按 token 步进，减少 DMA 次数。
- `ssm_state_indices` + `num_accepted_tokens` 驱动选择性状态写回，MTP 不再需要 Python 端 scatter；保证下一轮推理 state 正确，是启用 MTP 的前提之一。
- 状态矩阵 `stateOut` 直接复用 `state` 存储（in-place），节省 HBM 写回带宽。
- 使能方式：环境变量 `ENABLE_ASCENDC_FUSION_GDN="true"`。
- MTP 与 C8 互斥（README 约束 3）：当前融合算子在 C8 KVCache 路径未打通。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/qwen3-next/ops/gated_delta_net/recurrent_gated_delta_rule/recurrent_gated_delta_rule.cpp`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/qwen3-next/ops/gated_delta_net/recurrent_gated_delta_rule/recurrent_gated_delta_rule.cpp)（`TORCH_LIBRARY_IMPL(npu_ops_transformer_ext, ...)` 注册）、`op_kernel/recurrent_gated_delta_rule.h`。调用路径分两个阶段：`patches/stage3/0001-feat-GDN-adaption-and-support-MTP.patch` 的 `fused_recurrent_gated_delta_rule_update_npu` 走 `torch_npu.npu_recurrent_gated_delta_rule` 原生 API；`patches/stage5/0001-feat-support-GDN-and-rmsnormgated-fusion-ops.patch` 切换到自研 op 入口 `torch.ops.npu_ops_transformer_ext.recurrent_gated_delta_rule(mix_qkv, ssm_state, ..., nk=num_heads, nv=num_value_heads, ...)`（与自研 `.cpp` `TORCH_LIBRARY_IMPL` 签名匹配，亦见 `ops/npu_ops_transformer_ext/README.md` 注册入口列表）。README "新增特性使能" 表。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/qwen3_5/models/modeling_qwen3_5_moe.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/models/modeling_qwen3_5_moe.py)（`Qwen3_5MoeGatedDeltaNet._forward_decode` 调 `torch_npu.npu_recurrent_gated_delta_rule`）。MR!402（分支 chy_new "support qwen3_5"）。

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

<!-- cannbot:related:start -->
## 相关

- [MTP Speculative Decoding](../techniques/mtp_speculative_decoding.md)（`related`）：Qwen3-Next 的 MTP 只将 `num_accepted_tokens[i]` 指向的中间状态写回 `ssm_state`，避免拒绝 token 污染递归状态。
- [Qwen3-Next](../models/qwen3_next.md)（`related`）：- 位置：Qwen3-Next 每层 GDN 的 Decode 路径末端，替换原 `fused_recurrent_gated_delta_rule_update` Triton/Python 实现。；MTP 等一次验证多个 token 的路径还必须根据接收结果选择性回写 GDN 状态，避免下一轮读取未被接受 token 的状态。。模型卡给出 MTP 选择性回写 GDN 状态的正确性约束，kernel 卡定位到 Qwen3-Next decode 末端并实现该状态更新。
- [Qwen3.5-MoE](../models/qwen3_5_moe.md)（`related`）：“Decode 阶段两者都用 `npu_recurrent_gated_delta_rule`（［recurrent-gated-delta-rule］(../kernels/recurrent_gated_delta_rule.md)）。”；“｜ ［qwen3-5-moe］(../models/qwen3_5_moe.md) ｜ torch_npu 原生 API（`Qwen3_5MoeGatedDeltaNet._forward_decode`） ｜ `torch_npu.npu_recurrent_gated_delta_rule` ｜ 否（源未披露 Qwen3.5 的 AscendC 内部实现） ｜”。模型侧 Decode 调用与 kernel 卡的逐模型入口表完全对应，形成调用到实现边界的直接链路。
- [混合线性注意力 (Mamba / Gated-DeltaNet) 昇腾部署的精度陷阱清单](../../runbooks/precision/precision_mamba_gdn_linear_attention.md)（`related`）：一旦把某激活（此处 GDN gating 的 beta `sigmoid`）下沉进融合算子内部，产出该值的 gating 函数就改成返回 **raw**（未激活）值——此后所有**不走**该融合算子的回退/旁路分支必须自行补回该激活，否则精度错误：；Decode/MTP 阶段 ［gated-deltanet］(../modules/gated_deltanet.md) 的融合算子，用于混合注意力模型（［qwen3-next］(../models/qwen3_next.md)、［qwen3-5-moe］(../models/qwen3_5_moe.md)）线性注意力层的单步/少量 draft token 递推。一次 kernel launch 完成 Sigmoid + L2Norm + Gated Delta 递推注意力 + `ssm_state` 选择性更新，消除 Decode GDN 路径多个小算子的 Launch 和中间搬运开销。BF16 输入输出、FP32 累加，AIV 单元执行（`KERNEL_TYPE_AIV_ONLY`）。运行手册的旁路补激活规则由该融合算子内部执行 Sigmoid 的合同直接解释。
<!-- cannbot:related:end -->
