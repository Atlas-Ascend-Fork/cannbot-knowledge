---
type: Concept
title: SASG（SparseAttnSharedkvGrad，DeepSeek-V4 SAS 训练反向算子）
description: DeepSeek-V4 SAS 训练反向的五阶段流水与当前 TND SMLAG 绑定，区分四路主梯度、teacher carrier 和独立 Indexer 梯度。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v4/sparse_attn/ascendc.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v4/lightning_indexer/ascendc.py
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:39:13Z'
platforms:
- a3
---

# SASG（SparseAttnSharedkvGrad，DeepSeek-V4 SAS 训练反向算子）

## Summary

`SparseAttnSharedkvGrad`（**SASG**）是 [sparse-attn-sharedkv](../../../inference/concepts/kernels/sparse_attn_sharedkv.md)（SAS，DeepSeek-V4 统一 Attention 融合算子）的**训练反向**融合算子。它在 cann-recipes-train 的 DeepSeek-V4-Flash TorchTitan-NPU 续训练实践中，与 [slig](slig.md)（Lightning Indexer 反向 + KL Loss）一道补齐 V4 稀疏注意力的反向链路——推理侧 cann-recipes-infer 只有 SAS / [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md) 正向算子，SASG 是训练侧新增件。

它与 V3.2 DSA 的反向算子 [sfag](sfag.md)（SparseFlashAttentionGrad）同属一脉、角色对应，但针对的是 V4 的 **SAS 统一算子**：SAS 以单一接口按 `cmp_ratio` 覆盖**滑窗（SWA）/ 压缩（CFA）/ 稀疏压缩（SCFA）**三种 Multi-Query Shared-KV Attention，SASG 因此要为这套组合场景计算 `query / ori_kv / cmp_kv / sinks` 四路梯度。当前 TorchTitan-NPU 通过 sparse_attn.asc override 的 TND autograd 桥接 sparse_flash_mla_grad；旧 deepseek_v4_sfa converter 和 BSND 包装器已移除。

## SAS 正向回顾（反向的依据）

SASG 的输入大量来自 SAS 正向保存的中间量，先回顾 SAS 正向计算（详见跨域页 [sparse-attn-sharedkv](../../../inference/concepts/kernels/sparse_attn_sharedkv.md)）。SAS 完成的核心是 Multi-Query Shared-KV（$\tilde{K}=\tilde{V}$）带 Attention Sink 的 Attention：

$$S = Q @ \tilde{K}^\top,\qquad m = \max\bigl(\mathrm{sinks},\ \max(S)\bigr),\qquad \mathrm{Attention} = \frac{e^{S-m} @ \tilde{V}}{\sum e^{S-m} + e^{\mathrm{sinks}-m}}$$

其中 $\tilde{K}/\tilde{V}$ 是由 `ori_kv`（原始 KV，滑窗选取）、`cmp_kv`（Compressor 压缩后 KV）与 `cmp_ratio`（压缩比 1/4/128）共同控制的实际参与计算 KV。SAS 实现分 **V0/C1/V1/C2/V2** 五阶段（V 为 Vector、C 为 Cube）：

$$V_0:\ \mathrm{Gather}(\mathrm{cmpkv},\ \mathrm{topkIndices}[i]);\quad C_1:\ \mathrm{qk}=Q@K^\top;\quad V_1:\ P=\mathrm{onlineSoftmax}(\mathrm{qk},\mathrm{sinks});\quad C_2:\ O'=P@V;\quad V_2:\ O=\mathrm{rescale}(O')$$

正向流水通过 **Preload 一轮 V0+C1** 错开阶段依赖，实现除头尾外的 CV 流水并行：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/SAS-pipeline.png" width="58%"></p>
<p align="center"><sub>图：SAS 正向五阶段（V0/C1/V1/C2/V2）流水，Preload 一轮 V0+C1 实现 CV 并行（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·SparseAttnSharedkv）</sub></p>

反向要复用的正向产物即 `result`（attention 输出 $O$）与 `softmax_lse`（log-sum-exp，对应正向归一化分母），故正向调用必须开启 `returnSoftmaxLse=True`。

## SASG 反向计算流程

SASG 把 SAS 正向五阶段反传，主流程同样可分 **5 个阶段，依次为 Gather、Cube12、Process、Cube345、Scatter**：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/SASG-graph.png" width="62%"></p>
<p align="center"><sub>图：SASG 算子计算流程（Gather → Cube12 → Process → Cube345 → Scatter，逐路梯度 dQ/dKV/dSinks 反传）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·SparseAttnSharedkvGrad）</sub></p>

- **Gather**：按 `cmp_sparse_indices`（C4A 稀疏路径的 Top-k 索引）从压缩 KV 中离散提取本步需要的有效 K/V（对应正向 V0），是稀疏路径的离散访存入口。
- **Cube12 / Cube345**：两段 Cube 矩阵乘，承担 $dQ$、$d\tilde{K}/d\tilde{V}$ 反向链路中的若干 GEMM（反传 SAS 正向的 C1/C2）。源文档对 SASG 只给五阶段名、未列逐阶段公式；按标准 attention 反向推断，这两段大致覆盖 $Q@\tilde{K}^\top$、$P^\top@dO$、$dP@\tilde{V}$ 一类矩阵乘。
- **Process**：Vector 段，依据正向保存的 `softmax_lse` 重建在线 softmax 概率，并算 softmax 的雅可比反传（$dS$）、累计 sink 对分母的贡献得到 `sinks_grad`。
- **Scatter**：把离散位置上算出的 $d\tilde{K}/d\tilde{V}$ **ScatterAdd** 回 `ori_kv_grad` / `cmp_kv_grad` 的对应行（对应 Gather 的逆操作），因为 Shared-KV 下同一 KV 行可能被多个 query token 选中而需累加。

与 [slig](slig.md) / [sfag](sfag.md) 同源：稀疏 Top-k 选择带来 Gather / ScatterAdd 的**离散访存**，单次搬运量小，是该类反向算子共同的访存瓶颈来源。

## Pipeline 流水排布

> SASG 算子主流程可分为 5 个阶段，依次为 Gather、Cube12、Process、Cube345、Scatter，如图中所示。算子流水排布实现如下，通过 Preload 一次 Gather+Cube12 达成 CV 流水并行的效果。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/SASG-pipeline.png" width="60%"></p>
<p align="center"><sub>图：SASG 流水排布——Preload 一次 Gather+Cube12，使 Cube 与 Vector 阶段错开依赖、达成 CV 流水并行（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·SparseAttnSharedkvGrad）</sub></p>

排布思路与 SAS 正向（Preload V0+C1）、SLIG（V0 两次 Preload + PingPong）一致：**提前预取首段 Gather+Cube12**，让 Cube 段的算力与 Vector 段的访存/标量计算互相掩盖，消除朴素串行排布下 Cube/Vector 间的气泡。该批 V4 融合算子（LI / SAS / SASG / SLIG）的共同设计原则是从「负载均衡分核计算、内存与计算均衡」维度协同优化，充分释放芯片稀疏算力（源文档 Highlights）。

## 当前 op 与 autograd 绑定

`AscCompressedSparseInnerAttention` 使用 `_SparseFlashMLATND`：前向调用 cann_ops_transformer.sparse_flash_mla，保存 query、两路 KV、索引、sink、输出和 softmax_lse；反向调用 sparse_flash_mla_grad，返回 dquery、dori_kv、dcmp_kv、dsinks。LSE 只作为 teacher 中间量，不接收 loss 梯度。

当前布局为 TND，模型 B/L 轴合并，两路 KV 为单头，Top-k 索引与 teacher carrier 都按 [T,1,K] 传递。ratio=4 必须同时提供 cmp_k 与 topk_indices；ratio=128 不使用稀疏 Top-k。metadata 由本后端的 Config 在 microbatch 边界构建，CP 切分后重建，错误类型直接拒绝，不能继续使用旧不支持 TND 的 wrapper 签名。

SMLAG 的 cmp_softmax_l1 经无效槽清零和一次 softmax_scale 后，写入 topk_scores 梯度。配套 lightning_indexer.asc backward 再按整行 query 数归一并运行 SLIKG，负责 Indexer 的 dq/dk/dw；主注意力四路梯度与 Indexer 梯度分工保持明确。

arch22 通过 A3KeyWorkaround 压紧 gathered KV 到各文档可见范围，保证 mask 的 key-frame 锚点正确，压紧操作可微。硬件调用条件和 metadata 细节见 [SMLA](smla.md)。

## 来源报告的流水与当前实现

上文五阶段流水和图示来自当前 Recipes 中保留的优化案例，说明融合算子的计算与调度设计；它不规定当前 Python 包装器的参数表。该案例的 A3 64 卡 BF16、4K、MTP1、1100 tokens/p/s 属来源报告，未在本次复核重跑。当前启动、override 和软件依赖应按最新训练入口配置。

## Evidence

- [deepseek-v4_torchtitan_npu_autofuse.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md)（primary）
- [ascendc.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v4/sparse_attn/ascendc.py)（implementation）
- [ascendc.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v4/lightning_indexer/ascendc.py)（supporting）

## Links

- [sparse-attn-sharedkv](../../../inference/concepts/kernels/sparse_attn_sharedkv.md)（跨域：SAS 正向算子，SASG 是其训练反向，共用 `sparse_attn_sharedkv` PyTorch 绑定扩展）
- [ascendc](../../../inference/concepts/frameworks/ascendc.md)（跨域：Ascend C 算子编程框架，本 kernel 的实现底座）
- [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md)（跨域：LI 正向算子，产 `cmp_sparse_indices` 喂 SAS/SASG C4A 稀疏路径）
- [slig](slig.md)（同批：LI 反向 + KL Loss，与 SASG 分工承接 V4 稀疏注意力训练反向）
- [sfag](sfag.md)（同源对应：V3.2 DSA 的 SFA 反向算子，SASG 之于 SAS 等价于 SFAG 之于 SFA）
- [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)（承载实践：DeepSeek-V4-Flash A3 64 卡 BF16 续训练，1100 tokens/p/s）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba) — [`docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md`](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md)（高性能融合算子优化 / SparseAttnSharedkvGrad）
