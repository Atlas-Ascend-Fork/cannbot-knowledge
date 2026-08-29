---
type: Optimization
title: DSA 稀疏 Prefill 的 MLA 计算流按序列长度选型：短序列走 MHA+Mask、长序列走 Absorb+Sparse
description: DSA 稀疏 Prefill 的 MLA 计算流按序列长度选型：短序列走 MHA+Mask、长序列走 Absorb+Sparse。在 DSA 稀疏注意力（每 q token 经 Lightning Indexer 选 TopK≈2048 个 kv token）的 MLA prefill，要在三种 MLA 计算流之间选一种。「长序列一律 Absorb+Sparse」在短序列上并非最优——需按序列长度分档。
tags:
- task.optimization
- topic.attention
- topic.long_context
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/55
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/3
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# DSA 稀疏 Prefill 的 MLA 计算流按序列长度选型：短序列走 MHA+Mask、长序列走 Absorb+Sparse

## 适用场景

在 [DSA](../../../concepts/modules/dsa.md) 稀疏注意力（每 q token 经 [Lightning Indexer](../../../concepts/kernels/lightning_indexer.md) 选 TopK≈2048 个 kv token）的 [MLA](../../../concepts/modules/mla.md) prefill，要在三种 MLA 计算流之间选一种。「长序列一律 Absorb+Sparse」在短序列上并非最优——需按序列长度分档。

## 三方案速览（机制详见 weight-absorption 页，此处只给选型要点）

- **方案一 Naive + Sparse Mask（MHA 形态）**：每 q token 与全部历史 kv 算 attention、softmax 前用 mask 滤掉非 TopK。计算量等同全量 attention、拿不到稀疏收益，但 KV 一次性连续搬上片、后续复用片上数据，**无访存放大**。
- **方案二 Naive + Sparse Attention**：每 q token 只与 TopK 算。BMM 的 M 轴=1（GEMV 低效），且 HBM 访存相较全量激增约 2048×，访存瓶颈严重——**通常不选**。
- **方案三 Absorb + Sparse Attention**：M 轴=128（GEMM 友好）、HBM 访存相较方案二再降几十倍，与 decode 的 absorb 计算流归一；相对方案二计算量增约 3×。

三方案的 BMM shape 表与访存推导见 [mla-weight-absorption-latent-kv](mla_weight_absorption_latent_kv.md)，此处不复制。

## 选型规则（维护者确认，guide 正文未写短序列例外）

- **短序列（<4K）→ 方案一（MHA + Sparse Mask）**：稀疏收益小，而方案二 / 三要付 M 轴退化或访存放大代价不划算，退回 MHA 形态整体更优。
- **长序列 → 方案三（Absorb + Sparse）**：DSA 稀疏收益主导，方案三兼顾矩阵乘友好（M=128）与低访存，成为 Prefill / Decode 归一方案。
- **对照（非 DSA 的 DeepSeek v3.1）**：Prefill 建议 MHA、Decode 建议 MQA。

`<4K` 是维护者答复给出的经验阈值、无独立复测；本仓 inference guide 正文只无条件写「长序列→方案三」。

## 参考实现及其约束

参考 cann-recipes-infer 的 [DeepSeek-V3.2-Exp](../../../concepts/models/deepseek_v3_2_exp.md)：prefill CP 路径 `forward_absorb_cp` 与 decode `forward_absorb` 均走 absorb kernel（方案三归一）。方案取舍的 BMM shape / 倍数为本仓 doc 的设计分析（非独立复测 benchmark）；`<4K` 阈值属维护者经验值。规则限定到 DSA / Lightning-Indexer 稀疏 MLA 的 prefill，不外推到稠密注意力。权重吸收本身（GEMV→GEMM、砍 headnum 倍离散访存）与 absorb 的临界点讨论见 weight-absorption 页；[稀疏 FA 算子](../../../concepts/kernels/sparse_flash_attention.md)承载方案二 / 三的 TopK 计算。稀疏 MLA prefill 的 KV cache 写入另有 CP 两段式坑，见 [mla-prolog-zigzag-cp-kv-write](mla_prolog_zigzag_cp_kv_write.md)。

## Evidence

- `doc 披露`（@fa6892b / @239c0c1a）：`deepseek_v3.2_exp_inference_guide.md`「MLA Naive vs Absorb」节三方案定义、BMM shape、「方案二 M=1 + 访存 2048×」「方案三 M=128 + 访存比方案二降几十倍」「实践选方案三归一 Prefill/Decode」。`forward_absorb_cp`/`forward_absorb` 存在为 diff 事实。溯源下探 [cann-recipes-infer-pr-3-feat-add-deepseek-v3-2-exp-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/3)。
- `维护者确认`（@239c0c1a）：短序列（<4K）→方案一、长序列→方案三，及 v3.1 prefill=MHA / decode=MQA；guide 正文不含 `<4K` 阈值（grep 确认）、属事件独有经验。提问者的「方案二计算量是方案三 1/3」「M=1 因 16×16 tile 降十几倍」为提问者推断、未被逐条确认，本页不据此断言具体倍数。溯源下探 [cann-recipes-infer-issue-55-question-npu-deepseek-v3-2-exp-mla](https://gitcode.com/cann/cann-recipes-infer/issues/55)。

<!-- cannbot:related:start -->
## 相关

- [MLA 访存 / 显存优化：优先权重吸收（absorb）+ latent-KV 缓存；稀疏 / 长序列 prefill 选 Absorb+Sparse](mla_weight_absorption_latent_kv.md)（`related`）：三方案的 BMM shape 表与访存推导见 ［mla-weight-absorption-latent-kv］(mla_weight_absorption_latent_kv.md)，此处不复制。；**方案三 Absorb + Sparse Attention（推荐）**：相对方案二计算量增约 3 倍，但 BMM 的 M 轴变为 128（GEMM 友好），HBM 访存量相较方案二降几十倍，且与 decode 的 MLA 计算流归一（同一套 absorb 计算流，简化融合 kernel 设计）。。左卡把 DSA prefill 的按长度选型依据明确下钻到右卡，右卡提供方案三的 GEMM、访存与计算代价；阅读右卡可解释左卡为何在长序列选 Absorb+Sparse。
<!-- cannbot:related:end -->
