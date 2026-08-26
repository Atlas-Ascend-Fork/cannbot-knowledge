---
type: Guide
title: 块稀疏 Attention 与 Ulysses 序列并行同时使能（看全序列 + 规范序重映射 + head 负载均衡）
description: 块稀疏 Attention 与 Ulysses 序列并行同时使能（看全序列 + 规范序重映射 + head 负载均衡）。长序列视频 DiT 想同时吃到两种降本：块稀疏 Attention（TopK/SVG 丢弃低注意力块）减计算量，Ulysses 序列并行摊显存/时延。两者天然冲突，直接叠加会算错，须解决三处问题。单卡稀疏使能本身见 video-dit-blockwise-sparse-attention，Ulysses 本体见 video-dit-ulysses-sequence-parallel。
tags:
- task.debugging
- topic.attention
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/353
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 块稀疏 Attention 与 Ulysses 序列并行同时使能（看全序列 + 规范序重映射 + head 负载均衡）

## 适用场景

长序列视频 [DiT](../../../concepts/modules/dit.md) 想同时吃到两种降本：[块稀疏 Attention](../../../concepts/modules/blockwise_sparse_attention.md)（TopK/SVG 丢弃低注意力块）减计算量，[Ulysses](../../../concepts/parallelism/ulysses.md) 序列并行摊显存/时延。两者天然冲突，直接叠加会算错，须解决三处问题。单卡稀疏使能本身见 [video-dit-blockwise-sparse-attention](../../../optimizations/experience/rules/video_dit_blockwise_sparse_attention.md)，Ulysses 本体见 [video-dit-ulysses-sequence-parallel](../../../optimizations/experience/rules/video_dit_ulysses_sequence_parallel.md)。

## 三处冲突与手段

### 1. 稀疏块索引需要看到完整序列，而 Ulysses 把序列切到各卡

对 img q/k/v 做 all-to-all，从**序列并行布局切到头并行布局**，让每卡对自己负责的 head 持有**完整序列**，稀疏块选择因而在全序列上进行；attention 算完再 all-to-all 切回序列并行布局。txt token 走本地头切分（非整除 head 用 UAA，见 [ulysses-head-seq-divisibility-uaa](../../../runbooks/runtime/ulysses_head_seq_divisibility_uaa.md)）。

### 2. Ulysses 切分后各卡本地 token 顺序 ≠ 规范顺序，直接选稀疏块会错位

做稀疏 attn 前把本地 token 顺序 `index_select` 重排回规范（canonical）顺序（只对 img token 段重排、ctx 段原样拼回），在规范顺序上算稀疏 attn，算完再反向 remap 回本地顺序。规范↔本地双向索引按 `(frame_num, frame_patch_h, frame_patch_w, ulysses_world_size)` 计算并缓存。若稀疏前缀长度 < 序列长度，对后缀补一段稠密 attention（FIA）再拼接。

### 3. 各 head 稀疏度异构导致按 head 均分卡时计算量不均、出现拖尾

Ulysses 按 head 均分卡，而块稀疏下不同 head 稀疏度不同——按 head 序号均分时各卡实际计算量（∝ 稠密度 `1 - sparsity`）不均，最慢卡拖尾整个 step，`ulysses_degree` 越大越突出。手段：**按稠密度做贪心负载均衡**——对每个 `(step, layer)` 把 head 按稠密度降序，逐个塞进当前累计计算量最小的 rank（LPT 最长处理时间贪心），得到 per-`(step,layer)` 的 head 置换，head 切分前正向重排、算完逆重排，稀疏度向量按重排后顺序取用。仅 `ulysses_degree > 1` 启用。

上层按是否存在多卡 SP 上下文，在"多卡走并行稀疏路径 / 单卡走原稀疏 attention"间二选一。

## 收益（仓自报，无独立复测）

HunyuanVideo（Atlas 800I A2，异构稀疏 vs 稠密，DiT 计算耗时 s）：

| 方案 | 单卡 | 四卡(无均衡) | 四卡(均衡) | 八卡(无均衡) | 八卡(均衡) |
|---|---|---|---|---|---|
| 稠密 | 3587 | 904 | 904 | 464 | 464 |
| 异构稀疏 | 2160 | 576 | 564 | 335 | 321 |
| 相较稠密加速比 | 1.66x | 1.57x | 1.60x | 1.39x | 1.45x |

head 级负载均衡增量收益：四卡 `576→564`（~1.3%）、八卡 `335→321`（~4.2%）。仅陈述报告的这几组配置，不外推单调律；文档未给精度验证数据。

## 适用边界

证据覆盖 HunyuanVideo TopK/SVG 稀疏 + Ulysses 路径（`module/blockwise_sparse/sparse_method.py` 的 `forward_ulysses_sparse` / `_apply_local_seq_remap_tensor` / `apply_head_reorder_for_load_balance`）。其中"Ulysses 本地 token 序 ≠ 规范序、稀疏块选择需先 remap"与"head 计算量异构须按稠密度负载均衡"两条原理，可迁移到其它"多卡按 head 切分、head 间计算量异构"的块稀疏/头异构 attention 并行场景；稠密 attention（各 head 计算量相同）无此不均衡。

## Evidence

- `diff 事实`（@a12b2affe2d0）：`forward_ulysses_sparse`（all-to-all 布局切换）、`_apply_local_seq_remap_tensor`（正向 remap→稀疏 attn→反向 remap）、`parallel_sparse_attention`（稀疏不足补稠密）、`apply_head_reorder_for_load_balance`（贪心 LPT + 逆置换）均为新增实际代码。
- `doc 披露`（本 PR 新增 `hunyuan_video_optimization.md` 表格）：上述加速比与负载均衡增量收益，仓自报、无独立复测。
- 溯源下探：[cann-recipes-infer-pr-353-feat-hunyuanvideo-support-ulysses-parallelism-with-block-wise-sparse-att](https://gitcode.com/cann/cann-recipes-infer/merge_requests/353)
