---
type: Optimization
title: Prefill MLA 并行选型：大请求量走纯 DP、少 / 长请求走 SP-TP-SP（RS+AG 保持层间序列切分）
description: Prefill MLA 并行选型：大请求量走纯 DP、少 / 长请求走 SP-TP-SP（RS+AG 保持层间序列切分）。在昇腾上部署 MLA 结构模型的 prefill，要为注意力部分选并行切分。MLA prefill 有两条互补路线——纯 DP 面向吞吐，SP-TP-SP 混合切分面向时延与负载均衡。选错会在长 / 短请求、请求疏密不同的负载下浪费算力或拉长 TTFT。
tags:
- task.optimization
- topic.attention
- topic.parallelism
- topic.long_context
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/17
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/72
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/462
  role: evidence
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/README.md
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:57:02Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
---

# Prefill MLA 并行选型：大请求量走纯 DP、少 / 长请求走 SP-TP-SP（RS+AG 保持层间序列切分）

## 适用场景

在昇腾上部署 [MLA](../../concepts/modules/mla.md) 结构模型的 prefill，要为注意力部分选并行切分。MLA prefill 有两条互补路线——纯 [DP](../../concepts/parallelism/data_parallel.md) 面向吞吐，[SP-TP-SP](../../concepts/parallelism/sp_tp_sp.md) 混合切分面向时延与负载均衡。选错会在长 / 短请求、请求疏密不同的负载下浪费算力或拉长 TTFT。

## 条件 → 优先选哪套

- 请求量较大 / KV-Cache 内存占用较高 → **纯 DP**：每卡全载权重、只存本卡请求的 KV（无跨卡冗余）、MLA 段无通信算子，请求量大时易用满算力拿高吞吐。
- 请求数较少 / 分布不均 / 单请求序列很长（如 1 个 128K 请求）→ **SP-TP-SP**：把 batch·seq 合轴的 token 均匀切到各卡，MLA 计算负载均匀、长序列 TTFT 更短。

## 依据 — 两路各自的代价

- **纯 DP 的短板**：① 计算负载不均——请求序列长短参差，短序列卡提前算完要等批内最长序列，浪费周期；② TTFT 被拉长——实时请求数低于卡数时部分卡空闲，凑批延迟或处理不完整批都劣化。
- **SP-TP-SP 的代价**：① 每卡需存完整 KV-Cache（卡间冗余、内存高，可分卡存储规避）；② 相对纯 DP 引入 AllGather + AllToAll 通信（该通信可再用 micro-batch 双流掩盖，见 [prefill-micro-batch-dual-stream-moe-overlap](../../guides/optimization/prefill_micro_batch_dual_stream_moe_overlap.md)）。

## SP-TP-SP 怎么切（参考流程）

1. 多请求序列拼接并 pad 到卡数最小整数倍，对 batch 与 seq_len 合轴后的 token 做 SP 均匀切分，每卡等量 token。
2. FlashAttention 段用 [TP](../../concepts/parallelism/tensor_parallel.md)：attention head 均分各卡，计算负载均衡。
3. FA 后经 AllToAll 把 TP 转回 SP（此时通信量更小）；o_proj 因需全载权重，占用内存上升。

## 关键实现 — 用 ReduceScatter + AllGather 取代 AllReduce，保持层间序列切分

SP 打开时（守卫 `is_sp = tp_size>1 and attn_dp_size>1`），把 MLA 输出端的 `AllReduce(O)` 拆成 `ReduceScatter(O)` + 下一层入口 `AllGather(input)`，让层间 hidden 在 TP 维保持切分 `[T/tp, H]` 而非还原成全量 `[T, H]`：

- MLA 入口 `all_gather_into_tensor` 把本 rank 的 `[T/tp, H]` 聚成 `[T, H]` 做 attention；输出端 `reduce_scatter_tensor` 散回 `[T/tp, H]`。
- 收益：层间的 RMSNorm / Dense-MLP 计算量 ÷ attn_tp、层间残差激活同比例减少；通信量与 AllReduce 数学等价（ring AllReduce ≡ ReduceScatter + AllGather 两阶段）。
- 只在 prefill 触发；**decode 不用**——`batch_per_dp_rank` 可能小于 attn_tp，pad 浪费抵消收益，decode 保留 `all_reduce`。
- packed 变长细节：SP 用 all_gather 把 `T_local` 撑到 `T_padded`，但框架 metadata（slot_mapping/cu_kv）按 `T_real` 定尺寸；FA + cache 写入前把 hidden/cos/sin slice 回 `T_real`，reduce_scatter 前再 pad 回 `T_padded` 对齐反向通信形状；`position_ids` 保持 `T_real` 使 rotary_emb 产出 `T_real` 的 cos/sin。

这与「对访存 / 内存重的投影层单独局部 TP」是正交手段（后者见 [local-tp-memory-heavy-projections](local_tp_memory_heavy_projections.md)、[dp-attention-tp-oproj-mlp-hybrid](local_tp_memory_heavy_projections.md)）；用融合通算算子（AllGather-MM / MM-ReduceScatter）进一步掩盖投影层通信见 [hide-moe-attention-tp-ep-comm](hide_moe_attention_tp_ep_comm.md)。

## benchmark（仓自报，无独立复测）

SP RS+AG（LongCat-Flash-Lite，EP=8，昇腾 8 卡）两组受控点：

| 配置 | Prefill 无 SP | Prefill SP | Δ |
|---|---|---|---|
| EP=8 batch=8 | 199.91 ms | 145.22 ms | −27% |
| EP=8 batch=2 | 66 ms | 65 ms | 持平 |

**反例 / 边界**：batch=2（单请求 ~256 token、T 偏小）时 SP 省的 norm/MLP 算力被 RS+AG 同步开销抵消，持平；收益需更大 batch 或更长输入才显著。只此两点，不外推「越大越好」。

## 参考实现及其约束

- 纯 DP / SP-TP-SP 两套切分参考 [DeepSeek-R1](../../concepts/models/deepseek_r1.md) / [Kimi-K2](../../concepts/models/kimi_k2_thinking.md)（当前Kimi-K2-Thinking为独立MLA副本，Atlas A3）的 prefill 配置（按最新R1配置目录选择，历史rank数不构成当前YAML文件名）；选型规则来自本仓一手 prefill 优化文档。
- RS+AG 层间保切分的实现参考 [LongCat-Flash-Lite](../../concepts/models/longcat_flash_lite.md) 的 MLA `_forward_prefill`（`is_sp` 守卫、attn_tp=4 + attn_dp=2）。约束限定到 MLA prefill 且 attn_tp>1 且 attn_dp>1；技术思想（层间保持序列切分省 per-layer 计算 / 激活）可迁移到同类 MLA + EP 结构，具体收益随 batch / 序列长度而定。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/17)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/72)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/462)（evidence）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/README.md)（implementation）
- [modeling_longcat_flash_lite.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py)（implementation）
