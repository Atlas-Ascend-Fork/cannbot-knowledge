---
type: Guide
title: KVP — 长序列 memory-bound decode 沿 S 维切 KV Cache（lse-softmax 在线归约 + 耦合配置约束）
description: 适用：长序列 decode 且 KV Cache 内存/访存是瓶颈（单 rank 存完整 KV Cache 触发 device OOM 或抬高 decode 时延，memory-bound）；结构为 mla + MoE（KV 沿 S 维可切），本仓在 longcat-flash 落地。维护者确认收益针对 decode / PD 混合部署。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.speculative_decoding
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/215
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/246
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# KVP — 长序列 memory-bound decode 沿 S 维切 KV Cache（lse-softmax 在线归约 + 耦合配置约束）

## 适用场景 / 何时不适用

**适用**：长序列 **decode** 且 KV Cache 内存/访存是瓶颈（单 rank 存完整 KV Cache 触发 device OOM 或抬高 decode 时延，memory-bound）；结构为 [mla](../../../concepts/modules/mla.md) + MoE（KV 沿 S 维可切），本仓在 [longcat-flash](../../../concepts/models/longcat_flash.md) 落地。维护者确认收益针对 **decode / PD 混合部署**。

**不适用**：prefill（长序列 prefill 摊注意力走 [long-seq-prefill-context-parallel](../../../optimizations/experience/rules/long_seq_prefill_context_parallel.md) 的 CP，不是 KVP）；短序列 / 非 memory-bound。默认关闭（`kvp_size: 1`），仅长序列 decode 场景开。

## 机制（[kvp](../../../concepts/parallelism/kvp.md) 的可迁移核心）

连续 `kvp_size` 个 rank 组成一个 `kvp_group` 共同持有一份完整 KV Cache，组内各 rank 各存 `1/kvp_size` 分片；有效 attention-DP 组数 = `world_size // kvp_size`，组内 batch 复制。三段关键手段：

1. **KV 沿 S 维轮转分片（slot_mapping）**：`pos % kvp_size == kvp_rank` 的位置归当前 rank，其余槽写 `-1`（跳过），该 slot_mapping 作为 KV 写入算子（`npu_kv_rmsnorm_rope_cache`）的 index 把完整 KV 轮转分散写入各 rank：
   ```python
   mask = slot_mapping % self.kvp_size != self.kvp_rank
   return torch.where(mask, -1, slot_mapping // self.kvp_size + self.kv_len_offset[...])
   ```
   配套 `actual_seq_lengths_kv` 每 rank 调为 `//kvp_size + (%kvp_size > kvp_rank)`。

2. **decode 归约 = partial attention + lse-softmax 在线加权（关键，勿被文档误导）**：每 rank 用完整 `num_heads_per_rank` 对本地 `1/kvp_size` KV 分片调 [fused-infer-attention-score](../../../concepts/kernels/fused_infer_attention_score.md)（`softmax_lse_flag = kvp_size>1`）得 `attn_partial` / `lse_partial`；做**两次独立 all_to_all**（attn 与 lse dtype 不同，不可合并）按 head 维重分布到每 rank `num_heads_per_rank // kvp_size` 头的跨全 KV 结果；归约用 lse 的 softmax 加权求和**内联**完成（在线-softmax / log-sum-exp 合并）：
   ```python
   attn_output = (attn_scatter * lse_scatter.softmax(dim=0)).sum(dim=0)
   ```
   > ⚠️ 文档与合并代码不一致：doc 披露（`longcat_flash_optimization.md` 等）称归约由 `npu_attention_update` 算子完成，但 merged `forward_page_attention_absorb` **无该算子调用**，实际是上面的内联 lse-softmax 加权求和。做同类 seq-dim KV 并行归约时以此为准，勿照文档找 `npu_attention_update`。

3. **o_proj 复用 kvp_group all_reduce**：head 维 all_to_all 已把 head scatter 到各 kvp_rank，o_proj 在各 rank 出部分和后直接在 `kvp_group` 上 `all_reduce` 合并（故 `o_proj_tp_size == kvp_size`，旁路原 o_proj_tp 的 all2all+reduce_scatter）。因 attn-DP 组数变少，dense MLP / embed 的通信原语相应换为 all_reduce / 掩码分片 embedding。

## 前置条件（一组耦合硬校验，违反即 bring-up 期抛 ValueError）

`kvp_size > 1` 时并行配置必须同时满足——这组约束**相互耦合、源自 KVP 数据布局**，不是可自由调的旋钮，违反任一条切分后的 KV 分片 / partial 归约 / o_proj 通信宽度就对不齐：

| 约束 | 成因 |
|---|---|
| `world_size % kvp_size == 0` | KV 沿 S 交错切 `kvp_size` 份，需整除映射到 rank 组 |
| `o_proj_tp_size == kvp_size` | o_proj 走等宽 TP + all_reduce，宽度须与 kvp 对齐 |
| `attn_tp_size == 1` | Q/K/V head 维须完整才能与各 rank 的部分 KV 算 partial attention，不能再按 head TP |
| `cp_size == 1` | KVP 与 [context-parallel](../../../concepts/parallelism/context_parallel.md) 都沿 S 维切、互斥 |
| `batch_size % (world_size // kvp_size) == 0` | batch 需整除到 KVP 组外的 DP 维（`batch_size_per_rank = (batch_size*kvp_size)//world_size ≥ 1`） |
| `next_n == 0` | KVP 暂不支持 [mtp-speculative-decoding](../../../concepts/techniques/mtp_speculative_decoding.md)（MTP 投机） |

## 做什么（使能）

设 `parallel_config.kvp_size = K`，并按上表配齐 `o_proj_tp_size=K`、`attn_tp_size=1`、`cp_size=1`、`next_n=0`、`batch_size` 满足整除。样例：`world_size=32` → `kvp_size=8, o_proj_tp_size=8, attn_tp_size=1, batch_size=4`（`kvp_size*batch_size=32=world_size`）。

## 失败信号（配错时的 ValueError）

bring-up 启动期在 `check_parallel_settings` / `check_common_parallel_settings` / `check_model_settings` 直接拦截：
- `when kvp_size > 1, {attn_tp_size=} must be equal to 1`
- `when kvp_size > 1, {o_proj_tp_size=} must be equal to {kvp_size=}`
- `when kvp_size > 1, {cp_size=} must be equal to 1`
- `{kvp_size=} must be larger than {world_size // batch_size}`（来自 `kvp_size*batch_size//world_size < 1`）
- `{kvp_size=}, currently only support next_n = 0`

看到任一条即按上表调配置，而非绕过校验。

## Correctness / 收益 / rollback

- 收益：仓自报未给 before→after 量化数字（单点、无 baseline）；定性为长序列 KV 沿 S 切到多 rank，降单 rank KV 访存压力 / 避免 OOM，从而降 decode 时延。维护者确认针对 decode / PD 混合。
- rollback：`kvp_size: 1`（默认）关闭 KVP，所有 kvp 分支回落原 DP/TP 路径。

## 相关经验

- 另见 [跨 Prefill/Decode 默认 config 集群规模不一致 + 非默认卡数验证边界](../../../optimizations/experience/rules/prefill_decode_cluster_scale_mismatch.md)。


## Evidence

- **代码事实**（clone `@de084d3cc7fb`）：`models/longcat-flash/models/modeling_longcat_flash.py` 的 `forward_page_attention_absorb` / `get_slot_mapping` / `o_proj_forward` — slot_mapping 轮转、`actual_seq_lengths_kv` 调整、decode partial+lse 内联归约、o_proj kvp_group all_reduce 均对上 merged diff；同源的 `check_parallel_settings` 含 5 条 `raise ValueError` 约束。
- **代码事实**（clone `@d6ba03b342ef`）：`check_common_parallel_settings` 的 divisibility 键集含 `kvp_size`，与 `config/README.md` 注释一致。
- **维护者确认**：组内同 batch、`%kvp_size!=kvp_rank` 分片、收益针对 decode / PD 混合。
- ⚠️ doc 与代码不符处（归约算子）以一手代码为准，见机制第 2 点。
- 溯源下探：
  - [cann-recipes-infer-pr-215-feat-support-kvp-feat-for-longcat-flash-inference](https://gitcode.com/cann/cann-recipes-infer/merge_requests/215)
  - [cann-recipes-infer-pr-246-fix-revise-check-common-parallel-settings-and-check-parallel-settings-fo](https://gitcode.com/cann/cann-recipes-infer/merge_requests/246)
