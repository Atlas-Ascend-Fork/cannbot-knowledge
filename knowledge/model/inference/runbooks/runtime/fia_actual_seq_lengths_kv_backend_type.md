---
type: Runbook
title: FIA 的 actual_seq_lengths_kv 类型随后端不同：torch.ops.npu/npugraph_ex 要 host list、torchair/ge_graph 要 Tensor
description: 经 torch.ops.npu（eager 及 npugraph_ex 的 torch.compile/dynamo 路径）时，dynamo 按 SymInt[] schema 校验该入参——传 Tensor 会失败，必须传 host Python list。 经 torchair（tng.ops，ge_graph）时，反而接受 Tensor。
tags:
- task.debugging
- topic.attention
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/408
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/462
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# FIA 的 actual_seq_lengths_kv 类型随后端不同：torch.ops.npu/npugraph_ex 要 host list、torchair/ge_graph 要 Tensor

## 信号（现象）

调用 [npu_fused_infer_attention_score](../../concepts/kernels/fused_infer_attention_score.md)（FIA）时，`actual_seq_lengths_kv` 传错类型会报 schema 不符：

- 经 `torch.ops.npu`（eager 及 npugraph_ex 的 `torch.compile`/dynamo 路径）时，dynamo 按 `SymInt[]` schema 校验该入参——**传 Tensor 会失败**，必须传 host Python list。
- 经 [torchair](../../concepts/frameworks/torchair.md)（`tng.ops`，ge_graph）时，反而**接受 Tensor**。

同一个 FIA 调用，两条后端对 `actual_seq_lengths_kv` 的类型要求相反。

## 触发条件

FA decode，模型跑不同 `exe_mode`：eager / ge_graph / [npugraph_ex](../../concepts/techniques/npu_graph_mode.md)（`torch.compile`）。framework 的 `forward_metadata` 同时带 `actual_seq_lengths_kv`（Tensor）与 `actual_seq_lengths_list_kv`（host list），FA op 句柄按模式取：ge_graph 用 `torchair.ops`(tng.ops)，eager/npugraph_ex 用 `torch.ops.npu`。观测于 Gemma-4 decode。

## 根因

npugraph_ex（`torch.compile`）下 FA 走 `torch.ops.npu.npu_fused_infer_attention_score`，dynamo 对 `actual_seq_lengths_kv` 强制 `SymInt[]` schema，Tensor 不符；ge_graph 走 `torchair.ops` 时该约束不适用、Tensor 反而 OK。

## 修法

按 `exe_mode` 取用不同来源的 `actual_seq_lengths_kv`——npugraph_ex 取 host list，其余取 Tensor：

```python
# Gemma4Attention.forward
if self.exe_mode == "npugraph_ex" and forward_metadata.actual_seq_lengths_list_kv is not None:
    actual_seq_lengths_kv = forward_metadata.actual_seq_lengths_list_kv[-bsz:]   # host list
    # dynamo enforces SymInt[] schema for actual_seq_lengths_kv — must be a host list, not a Tensor
else:
    actual_seq_lengths_kv = forward_metadata.actual_seq_lengths_kv               # Tensor
    if actual_seq_lengths_kv is not None and actual_seq_lengths_kv.shape[0] != bsz:
        actual_seq_lengths_kv = actual_seq_lengths_kv[-bsz:].contiguous()
```

## 另一参考实现：LongCat-Flash-Lite（同契约 + 算子入口按后端绑定 + 时延旁证）

[MLA](../../concepts/modules/mla.md) decode 用 FA v2（`npu_fused_infer_attention_score_v2`，`input_layout="TND_NTD"`）配 Paged Attention 读压缩 KV cache 的另一处实现，印证同一契约并补两点：

- **同契约扩到 cumulative q 偏移**：`enable_npugraph_ex` 时取 `actual_seq_lengths_list_kv` / `actual_seq_lengths_cu_list_q`（host list），否则取 `actual_seq_lengths_kv` / `actual_seq_lengths_cu_q`（Tensor）。即 npugraph_ex 的 list 要求不止作用于 `actual_seq_lengths_kv`，也作用于 `actual_seq_qlen`（cumulative q 偏移）。
- **算子入口也随后端绑定**：同一 MLA 模块按 `enable_gegraph` 分别绑定 `tng.ops`（[ge_graph](../../concepts/frameworks/torchair.md)）或 `torch.ops.npu`（其余）下的 FA 算子入口——把 FA 相关后端差异（**算子入口 + 变长实参形态**两处）集中在初始化与 decode 入口处理，模型主体逻辑不变。迁移一个已在 ge_graph 跑通的 FA/FIA 调用到 npugraph_ex（或反向）时，这两处都要核对，不要假设跨后端同形。
- **后端时延旁证**（源自报，A3 rank_8_8ep b=2）：ge_graph decode 8.10 ms vs npugraph_ex 9.11 ms——稳态 decode 上 ge_graph 整图优化更充分，npugraph_ex 慢约 12–17%，更适合编译启动敏感场景。此为后端选型旁证，与本页实参形态契约正交。

## 适用边界

op 级、可迁移：**任何用 FIA 且跑 npugraph_ex / torch.compile 的模型**都适用这条类型契约，不限 Gemma-4。注意与更早的 ge_graph 经验不冲突——某些报告曾记 ge_graph 把 list 改成 Tensor（只覆盖 ge_graph，npugraph_ex 相反要 list），两后端各自成立，非矛盾。

## 相关经验
- [把注意力映射到昇腾 FIA：attention sink / 滑窗 / 全窗的 sparse](../../optimizations/experience/rules/attention_to_fia_sparse_mode_sink_window.md)
- [FIA/qlens 的 block_table 首维 / num_reqs / TND se](fia_qlens_block_table_num_reqs_batch_contract.md)
- [昇腾编码器 packed 全注意力：两个可互换融合算子的 seq_len 语义不同（unpa](mm_encoder_packed_attention_seqlen_semantics.md)

- 另见 [变长 Prefill 的 MLA FlashAttention 布局选 NTD（免 padding 又避 TND 的转置 / 带宽损失）](../../optimizations/experience/cases/mla_prefill_flash_attention_ntd_layout.md)。
- 另见 [FIA 的 MLA 无量化路径硬约束 group_num ∈ {2 的幂}（否则 561002 / CheckFeatureMlaNoQuantShape 失败）](../compilation/fia_mla_noquant_group_num_power_of_two.md)。
- 另见 [CUDA 原生 vLLM 多模态模型移植 vllm-ascend NPU：三处固定后端不兼容点与修法](vllm_cuda_multimodal_npu_bringup.md)。
- 另见 [KVCache 静态化 + FA / FIA 融合算子替换的精度陷阱](../precision/precision_kvcache_fa_fusion_pitfalls.md)。


## Evidence

- **代码事实**（clone `@8721be444490`，修复 commit `654db24d7546` "npugraph_ex compat — read actual_seq_lengths_kv host list from forward_metadata"）：`Gemma4Attention.forward` 按 exe_mode 分支取用 `actual_seq_lengths_kv`——npugraph_ex 取 host list、其余取 Tensor；diff 内带代码注释 "dynamo enforces SymInt[] schema for actual_seq_lengths_kv — must be a host list, not a Tensor"。
- **仓自报**（优化 report 披露）：ge_graph 曾把 list 改成 Tensor（早于 npugraph_ex 支持，只覆盖 ge_graph；npugraph_ex 相反要 list），两后端各自成立、非矛盾。
- 溯源下探：[cann-recipes-infer-pr-408-feat-add-gemma-4-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/408)
- **代码事实**（LongCat-Flash-Lite，clone `@895615c`）：`LongcatFlashMLA._forward_decode_prolog` 的 `enable_npugraph_ex` 分支切换 `actual_seq_lengths_list_kv` / `actual_seq_lengths_cu_list_q`（list）与 Tensor 变体；同模块按 `enable_gegraph` 绑定 `tng.ops` / `torch.ops.npu` 的 FA 入口。时延数（ge_graph 8.10 ms vs npugraph_ex 9.11 ms）为源自报、无独立复测。
  - 溯源下探：[cann-recipes-infer-pr-462-refactor-longcat-flash-lite-tnd-pa-npugraph-ex-mc2-ep-decode](https://gitcode.com/cann/cann-recipes-infer/merge_requests/462)