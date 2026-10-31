---
type: Concept
title: SLIG（SparseLightningIndexerGradKLLoss，DSA 训练反向算子）
description: 当前 DeepSeek-V3.2 AscendC backend 的 SLIG：forward 零占位，backward 计算 Indexer 梯度和 KL，AuxLoss 按全局有效 token 归一化；保留来源的数学、Tiling 与离散访存优化。
tags:
- task.implementation
- topic.attention
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v3_2/sparse_attn/ascendc.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v3_2/sparse_attn/__init__.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/fused_ops.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:39:13Z'
platforms:
- a3
---

# SLIG（DSA Indexer 梯度与 KL 损失）

## Summary

SLIG（SparseLightningIndexerGradKLLoss）训练 Indexer，使它的稀疏候选分布贴近主注意力的教师分布，融合 KL Loss 与 Indexer query/key/weights 的梯度。算子为 `torch_npu.npu_sparse_lightning_indexer_grad_kl_loss`；主注意力梯度仍由 [SFAG](sfag.md) 承担。

当前 TorchTitan NPU 在 `override.deepseek_v3_2.sparse_attn.asc` 中同时接入 attention 与它自己的 TND metadata，不再使用 npu_dsa converter/TOML 或旧 activation-checkpoint 状态门控。

## 计算逻辑


训练阶段需把 Lightning Indexer 的输出与 Sparse Flash Attention 的 softmax 结果对齐算 loss。记 $g$ 为 GQA group size、$d$ 为头维度、$S_k$ 为上下文长度：

1. **LI 正向 Top-k value**：$I_{t,:} = W_{t,:}\,@\,\mathrm{ReLU}(\tilde{q}_{t,:}\,@\,\tilde{K}_{topk,:}^\top)$（$\tilde{q}_{t,:}$ 为第 $t$ token 的 $g$ 个 query 头合轴结果，$\tilde{K}_{topk,:}$ 按 Top-k 索引取行）
2. **SFA 正向 Top-k value**：$p_{t,:} = \mathrm{Softmax}(q_{t,:}\,@\,K_{topk,:}^\top/\sqrt{d})$
3. **KL Loss**：$Loss = \sum_t D_{KL}(p_{t,:}\,\|\,\mathrm{Softmax}(I_{t,:}))$，$D_{KL}(a\|b)=\sum_i a_i\log(a_i/b_i)$；$p$ 为 target distribution（对所有 head 求和后沿上下文方向 L1 正则）
4. **梯度**：$dI_{t,:} = \mathrm{Softmax}(I_{t,:}) - p_{t,:}$
5. **链式法则**（$S=\tilde{q}@\tilde{K}^\top$，$dS$ 由 $dI$ 反传 ReLU）：
   $$dW_{t,:} = dI_{t,:}\,@\,(\mathrm{ReLU}(S_{t,:}))^\top,\quad d\tilde{q}_{t,:} = dS_{t,:}\,@\,\tilde{K}_{topk,:},\quad d\tilde{K}_{topk,:} = (dS_{t,:})^\top\,@\,\tilde{q}_{:t,:}$$
   $d\tilde{K}$ 为 Top-k 索引对应行的累加。

为平衡显存与算力，算子保留部分重要正向结果做**部分重计算**。


## 当前 autograd 时机与归一化

`_AscSparseIndexerLossFunc.forward` 保存主 Q/K、Indexer Q/K/weights、TopK、softmax_max/sum、RoPE 及长度信息，返回 FP32 **零标量**。它不在 forward 计算 SLIG，也不保存已经算出的三路梯度。

`backward(ctx, grad_scale)` 才调用融合 kernel，固定 `layout="TND"`、`sparse_mode=3`，返回的 Indexer 三路梯度乘上 grad_scale。该系数来自 `AuxLoss.inject`，已经包含 `coeff / global_valid_tokens`，不可再重复除以 batch*local sequence。主 Q/K、索引和 metadata 不通过这一 loss 分支求梯度。

融合算子只在 backward 产出 summed KL，当前实现把 `loss.squeeze() / AuxLoss._step_denominator` 累加到 instance_acc；必须先设置 step denominator。forward 交给 inject 的零占位不是真实 KL 指标，不能以其为零判断 Indexer 未训练。carrier 接主 attention 输出，保留主前向值并接入辅助梯度。

## TND 与 CP 输入

模型输入先由 `[B,L,N,H]` 折成 TND；LI 产 TopK 后，SFA 开 `return_softmax_lse=True`，为 SLIG 保留 max/sum。后端 `build_attention_metadata` 每个 microbatch 为相同几何构造共享 `AscVarlenMetadata`，把 Q/K 的累计结束 offset 一次搬到 host；它们不是逐段长度。

CP 使用 rank-local `CPVarlenMetadata`，根据 k_global_gather_indices 选择正确 key 行，并重建本 rank 的累计长度。不可复用旧 BSND/单段 slice_end 示例。入口声明同时派生 AscSparseIndexerLoss.Config，不需要独立 metadata override。

## Tiling 设计


- **核间**：对 B 和 S 轴分核切分。
- **核内**：基本块 $(128,128)$；L1 空间划分——$Q$ 矩阵 $128{\times}576{\times}2B=144\,\mathrm{KB}$ 常驻、$Q_{index}$ 启 Double Buffer 32 KB 常驻、$Gather$ 矩阵 DB 64 KB（每次搬 $(128,128)$）、$reluGrad$ 矩阵 288 KB（每次搬 $(64,2048)$）；L0A/L0B/L0C 启 DB（$2{\times}32/32/64$ KB）。$C_1$ 阶段含 $MatmulP$/$MatmulSy$，$C_2$ 阶段含 $MatmulDk$/$MatmulDq$，各自的 L0A/L0B 搬入块尺寸不同（如 $MatmulDk$ 为 $(128,64)/(64,128)$）。

## Pipeline 与离散访存优化

计算分五阶段：预处理 Gather（$V_0$）→ Matmul + ReLU（$C_1$）→ $V_1$ 多向量计算 → $C_2$ Matmul → 后处理 ScatterAdd（$V_2$）。相较 LI/SFA 正向，本算子流程更繁琐、数据依赖更复杂，朴素排布下 Cube/Vector 间气泡多，**提前 Preload 一次 $V_0$** 实现流水互相掩盖。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v32/b3eb5905-9d3c-4391-b6b8-21d6d098cd0d.jpg" width="62%"></p>
<p align="center"><sub>图：SLIG 五阶段流水，Preload V0 掩盖 Cube/Vector 气泡（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·SLIG Pipeline 设计）</sub></p>

$V_0$ Gather 与 $V_2$ ScatterAdd 需离散访存。非 Sparse 场景的 Attention 算子访存连续，单次搬运耗时长于指令下发耗时，可连续多次访存达到较高带宽；而 Sparse Attention 的离散访存单次耗时大幅下降，甚至**小于指令下发耗时**，于是退化为严重的指令下发阻塞（如下图，搬运被一连串指令下发卡住），这正是后续成对聚合优化要解决的问题。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v32/b97ed3e2-ca09-46f6-9f5d-2887c8bad304.png" width="50%"></p>
<p align="center"><sub>图：Sparse 离散访存单次量小 < 指令下发耗时，导致指令下发阻塞（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·离散访存优化）</sub></p>

两项优化：

- 利用 A3 **Cube:Vector = 1:2** 的核数比，用 Vector 核发射访存指令，下发效率翻倍。
- 离散数据点**两两聚合**，用 `srcGap` 参数成对访存提升带宽。
- **合轴**：不同 QueryToken 对应不同 KeyToken，故 N 轴放内层循环，B、S 轴作切分轴。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v32/31a06a5c-c7aa-4767-8cc3-76afb6628db0.png" width="52%"></p>
<p align="center"><sub>图：离散数据点两两聚合、srcGap 成对访存提升带宽（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·SLIG 离散访存优化）</sub></p>


## Evidence

- [deepseek-v32_pre_train_optimization.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md)（primary）
- [ascendc.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v3_2/sparse_attn/ascendc.py)（implementation）
- [__init__.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v3_2/sparse_attn/__init__.py)（implementation）
- [fused_ops.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/fused_ops.md)（supporting）

## Links

- [SFAG](sfag.md)
- [训练 CP](../parallelism/custom_cp_dsa.md)
- [TorchTitan 组件替换](../frameworks/npu_fused_op_converters.md)
- [V3.2 训练](../../guides/recipes/deepseek_v32_pretrain.md)
- [Lightning Indexer](../../../inference/concepts/kernels/lightning_indexer.md)
