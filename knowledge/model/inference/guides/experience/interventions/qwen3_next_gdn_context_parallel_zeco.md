---
type: Guide
title: ZECO — 让线性注意力 / GDN 吃到序列并行（Context Parallel），打破 chunk 递推的跨 rank 顺序依赖
description: 要给线性注意力层上序列并行 / Context Parallel（长序列 prefill、单卡 activation 显存不够 / OOM），但——；线性注意力的 chunk 递推状态跨 chunk 顺序依赖（h_t 要等 h_{t-1}），天然抗拒按序列切分：常见结果是全注意力层能吃 CP、线性注意力层只能回退 full Tensor Parallelism、拿不到序列并行的加速与省显存。
tags:
- task.debugging
- topic.model_architecture
- topic.attention
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/359
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/159
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# ZECO — 让线性注意力 / GDN 吃到序列并行（Context Parallel），打破 chunk 递推的跨 rank 顺序依赖

## 适用场景（问题信号）

在优化**线性注意力**（[GatedDeltaNet](../../../concepts/modules/gated_deltanet.md) / Mamba / DeltaNet 风格的 chunk 递推）时，遇到以下场景应想到 ZECO：

- 要给线性注意力层上**序列并行 / Context Parallel**（长序列 prefill、单卡 activation 显存不够 / OOM），但——
- 线性注意力的 **chunk 递推状态跨 chunk 顺序依赖**（`h_t` 要等 `h_{t-1}`），天然抗拒按序列切分：常见结果是全注意力层能吃 CP、**线性注意力层只能回退 full Tensor Parallelism**、拿不到序列并行的加速与省显存。

ZECO 就是让线性注意力突破这个「顺序依赖」、也能像全注意力一样切序列的算法。

## ZECO 是什么

线性注意力的 chunk 递推是**仿射线性**的：`h_t = A_t · h_0 + B_t`（`A_t`/`B_t` 只依赖本 chunk 的输入，与前序状态 `h_0` 无关）。据此可把「跨 rank 顺序算 h」拆成两步、让各 rank 并行：

1. **各 rank 先并行算本地 chunk 的状态转移系数 `(a, b)`**（不需要上游状态），与跨 rank 通信重叠。
2. **一次轻量的跨 rank 状态传播**得到每个 rank 的 initial_state，再用 `h_t = a·h_0 + b` 本地还原状态、出输出——不再需要按 rank 顺序滚算 `h`。

拓扑**非 ring**：首 rank 正常算出 final_state 沿链传播、末 rank 把 global final_state broadcast 给全组。于是线性注意力层也能沿序列维切到多 rank（CP），与全注意力层的 CP（ZigZag 负载均衡，见 [long-seq-prefill-context-parallel](../../../optimizations/experience/rules/long_seq_prefill_context_parallel.md)）配齐。

> 一句话：**利用 chunk 递推的线性性，把「顺序依赖的状态滚算」换成「并行算系数 + 一次状态传播」——这是 ZECO 可迁移到任意线性注意力 SP 场景的核心。**

## 参考实现：cann-recipes-infer（Qwen3-Next）

cann-recipes-infer 在 [qwen3-next](../../../concepts/models/qwen3_next.md) 上有一份可参考的 ZECO 实现，可直接借鉴其工程结构：

- **选路**：`chunk_gated_delta_rule_npu` 在 `cp_group is not None` 时走 `chunk_gated_delta_rule_zeco_fwd`；first_rank 与其它 rank 分别编排 `isend/irecv` + 独立 `comm_stream` 与计算重叠。
- **两个 [Triton-on-Ascend](../../../concepts/frameworks/tilelang.md) 核**：`chunk_delta_h_zeco.py`（a/b 系数核 + `chunk_final_state_zeco_kernel`）、`chunk_o_zeco.py`（输出核）。
- **框架元数据**（`AscendGDNAttnBackend.init_cp_metadata`）：切序列前按每卡重建 `query_start_loc`/`cu_seqlens`（均匀切分、余数摊到前几卡、`.clone()` 防改共享张量）；单 batch 走 `single_batch_overlapped_causal_conv1d_update`（isend 末尾 `overlap_size = weight.shape[1]-1` 个元素重叠 conv1d）。
- **使能**：`export ENABLE_CONTEXT_PARALLEL_GDN=1` + `--cp-size N`（替换 `--enable-dp-attention --dp-size N`）；env 打开后 `use_full_tp=False` → GDN 走 CP。

**该参考实现的约束**——照搬这套代码要受它们约束，迁移算法思想则不受：

- **GDN `head_dim` 硬编码 128**（`assert K==128`、无回退，维护者确认刻意如此）：其它 head_dim 的线性注意力模型上 CP 前须先确认或改核。
- **只针对单 batch 均衡切分**：多 batch 有代码路径但切分不按 batch 均衡，非目标场景。
- **SGLang + sgl_kernel_npu 的 fla 栈**、Atlas A3（910C）。
- **PD 分离**：`attn_tp_size` 不等时按 head 维切 Mamba/GDN state 做 M:N TP 传输（`send_mamba_state_slice`，要求 `state_type=="mamba"`、`attn_tp_size ≤ dst_attn_tp_size`）；PD 分离下强制 `swap_kv`，会破坏 chunked prefill 并带额外通信开销。

## Correctness / benchmark

- 数学正确性：CANN 审查确认 ZECO 数学正确、结论「建议合入」。
- benchmark（仓自报、无独立复测）：算子 `fla.chunk_gated_delta_rule_npu`（Atlas A3 / 910C，32 heads），从 **TP16**（GDN full-TP 回退）切到 **TP2+CP8**（ZECO CP GDN）：

  | Seqlen | Num Heads | TP16 | TP2+CP8 | 加速 |
  |--|--|--|--|--|
  | 65536 | 32 | 0.01625 | 0.00792 | 2.05x |
  | 131072 | 32 | 0.02996 | 0.01204 | 2.48x |

  （仅 2 个受控点，均在长序列单 batch 目标场景内，不外推「序列越长越快」单调律。）

- 端到端 TTFT（bfloat16，Atlas A3 / 910C，seqlen 65536，仓自报）：**TP16 2162.53 ms → TP2+CP8 1876.89 ms（≈ -13%）**。算子约 2x 的提速只传导到端到端约 -13%，因 GDN 只是整网的一部分；决定是否上 ZECO 时按「端到端占比」而非「算子加速比」估收益。同批另一次算子测量给 65536 档 0.01684 / 0.00853（≈2x），与上表量级一致（不同版本/次测量，精确值略异）。

## rollback

不设 `ENABLE_CONTEXT_PARALLEL_GDN`（GDN 回退 full-TP，功能不变）。

## 相关经验

- 另见 [混合线性注意力 (Mamba / Gated-DeltaNet) 昇腾部署的精度陷阱清单](../../../runbooks/precision/precision_mamba_gdn_linear_attention.md)。


## Evidence

- **代码事实**（clone `@d13c484`）：`models/qwen3-next/patches/stage6/0001-support-gdn-cp.patch` + `sgl_kernel_npu_support_gdn_cp.patch` + `README.md` 中，zeco 选路与 first/other-rank 通信编排、两处 `use_full_tp` gating、两个新 zeco 核、`init_cp_metadata` / `single_batch_overlapped_causal_conv1d_update`、conn.py 的 `send_mamba_state_slice` 均对上。
- **维护者确认**：非 ring 拓扑；GDN `head_dim` K=128 不设回退（刻意如此）。
- **仓自报**（无独立复测）：算子 benchmark 数字来自仓库描述表 + README；端到端 TTFT 与另一组算子表来自 RFC 的性能表（doc 披露）。
- 溯源下探：
  - [cann-recipes-infer-pr-359-support-context-parallel-execution-of-gateddeltanet-attention-in-qwen3-n](https://gitcode.com/cann/cann-recipes-infer/merge_requests/359)
  - [cann-recipes-infer-issue-159-rfc-support-context-parallelism-for-gateddeltanet-in-qwen3-next](https://gitcode.com/cann/cann-recipes-infer/issues/159)