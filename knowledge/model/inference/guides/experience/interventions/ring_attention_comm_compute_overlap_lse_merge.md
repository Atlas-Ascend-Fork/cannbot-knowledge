---
type: Guide
title: 多卡 Ring/序列并行注意力用异步 all-gather + 本地 FA + LSE 合并掩盖 KV 通信
description: 多卡（ring_world_size > 1）Ring / Unified-SP（Ulysses + Ring 两级）序列并行做长序列注意力时，KV 需跨 ring rank 汇聚。经典 Ring Attention 用逐步 P2P（send/recv）在环内轮转 KV，通信与计算难以充分重叠、且被拆成 ring_world_size-1 个串行小步。目标是让 NPU 的注意力计算与网络 KV 通信并行，把通信时延藏进本地注意力计算里。
tags:
- task.debugging
- topic.attention
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/220
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/92
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- a2
---

# 多卡 Ring/序列并行注意力用异步 all-gather + 本地 FA + LSE 合并掩盖 KV 通信

## 适用场景

多卡（`ring_world_size > 1`）[Ring](../../../concepts/parallelism/ring_attention.md) / Unified-SP（[Ulysses](../../../concepts/parallelism/ulysses.md) + Ring 两级）序列并行做长序列注意力时，KV 需跨 ring rank 汇聚。经典 Ring Attention 用逐步 P2P（send/recv）在环内轮转 KV，通信与计算难以充分重叠、且被拆成 `ring_world_size-1` 个串行小步。目标是让 NPU 的注意力计算与网络 KV 通信并行，把通信时延藏进本地注意力计算里。

不适用：单卡或 `ring_world_size == 1` 不进该路径。前置——注意力算子须能返回每段的 `softmax_lse`，否则无法做在线-softmax 合并。

## 做什么

用 all-gather 一次性收全环 KV，配合异步启动 + 本地先算 + LSE 合并，把通信掩盖在第一段本地注意力里。机制思想见 [ring-attention-overlap](../../../concepts/techniques/ring_attention_overlap.md)，流程：

1. **异步 all-gather 远端 KV**：对本 rank 的 `k`/`v` 发 `all_gather_into_tensor(..., async_op=True)` 拿 handle，不等待。
2. **立即算本地 FA（带 LSE）**：用本 rank 自己的 `q,k,v` 算第一段注意力得 `out_local, lse_local`——这段计算与上面的通信并行，是被掩盖的部分。
3. **等 gather 完成，取"其它 rank"的 KV**：`handle.wait()` 后，用缓存的 `other_indices`（除本 rank 外的所有环内 index）`index_select` 挑出远端分片。
4. **远端分片拼成一条长序列，一次性算第二段 FA**：把 `k_others/v_others` 合并为一条长 KV，用同一 `q` 算**一次**大注意力（`causal=False`），得 `out_others, lse_others`——不是逐 rank 多次小注意力。
5. **LSE 在线-softmax 合并两段**：以两段 LSE 的 max 为基做数值稳定的加权和，等价于对全 KV 做一次注意力：
   ```
   max_lse = maximum(lse1, lse2)
   lse_new = max_lse + log(exp(lse1-max_lse) + exp(lse2-max_lse))
   out = exp(lse1-lse_new)*out1 + exp(lse2-lse_new)*out2
   ```

**关键前置——拿到分段 LSE**：靠 [FIA](../../../concepts/kernels/fused_infer_attention_score.md) 的 `softmax_lse_flag=True` 输出每段 log-sum-exp；缺 LSE 则无法合并。

## 可迁移工程要点

- 这个 "Ring" 是**基于 all-gather** 的实现（一次收全环分片），不是经典 P2P 逐跳轮转 ring——沿用 "ring attention" 名称时注意语义差异。代价是远端 KV 缓冲 `[ring_world_size, b, s_local, n, d]` 显存随 ring 度线性放大，非经典 P2P 的常量额外显存。
- 缓存"排除自身 rank"的 index tensor（仅 `rank/ring_size/device` 变化才重建），避免每步重建 index 与随之的 host-device 同步。
- FIA 参数约定：`input_layout="BNSD"`；GQA 按 `num_key_value_heads`（`num_heads==num_key_value_heads` 时置 0）；非因果全注意力 `next_tokens = 65535`。

## correctness / rollback

- correctness 判据：重叠路径与非重叠回退（同步 all-gather 全 KV 后一次 FA、不带 LSE）经 LSE 在线-softmax 合并保持数值等价，二者互为对照。源未附独立精度对拍。
- rollback：置 `use_ring_overlap=False` 走非重叠 all-gather 全量注意力路径，天然回退基准。
- overlap 路径写死 `causal=False`（面向 DiT 全注意力），因果场景的分块可见性未在此路径处理。

## 参考实现

统一序列并行封装在 `module/unified_sp/core.py::UnifiedSPAttention`（`_ring_attention_overlap` / `_merge_two_outputs` / `_ring_attention_allgather` 回退 / `SPConfig.use_ring_overlap` 默认 True）。落地于 [Wan2.2-I2V](../../../concepts/models/wan2_2_i2v.md)、[HunyuanVideo](../../../concepts/models/hunyuan_video.md) 视频 [DiT](../../../concepts/modules/dit.md)（Atlas A2）。序列并行本体与整除约束见 [video-dit-ulysses-sequence-parallel](../../../optimizations/experience/rules/video_dit_ulysses_sequence_parallel.md)、[ulysses-head-seq-divisibility-uaa](../../../runbooks/runtime/ulysses_head_seq_divisibility_uaa.md)；长序列 prefill 的 CP 选型见 [long-seq-prefill-context-parallel](../../../optimizations/experience/rules/long_seq_prefill_context_parallel.md)。

## Evidence

- `diff 事实`（@28bf626f6a7d）：`_ring_attention_overlap`（异步 `all_gather_into_tensor(async_op=True)` → 本地 `_attention_with_lse` → `wait()` → `index_select` 远端 → reshape 合并 → 第二段 FA → `_merge_two_outputs`）、`_merge_two_outputs` 的 LSE 重加权公式、`_npu_attention_with_lse`（FIA `softmax_lse_flag=True`）逐条对上；Wan2.2-I2V 与 HunyuanVideo 均实例化 `UnifiedSPAttention(use_ring_overlap=True)`。
- 无实测加速数字；源仅给设计目标（把通信藏进本地计算）。"与全 KV 一次注意力等价"依 LSE 合并的数学性质与两条代码路径推断。
- 溯源下探：[cann-recipes-infer-pr-220-feat-support-for-communication-and-computation-overlap-in-ringattention](https://gitcode.com/cann/cann-recipes-infer/merge_requests/220) · [cann-recipes-infer-issue-92-rfc-wan2-2-i2v-hunyuan-video-ringattention](https://gitcode.com/cann/cann-recipes-infer/issues/92)