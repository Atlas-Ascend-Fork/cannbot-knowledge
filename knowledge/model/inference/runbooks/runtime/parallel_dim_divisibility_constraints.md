---
type: Runbook
title: 多卡 MoE/SP 部署的整除·对齐约束（batch↔EP、input_max_len↔attn-TP）
description: 多卡 MoE/SP 部署的整除·对齐约束（batch↔EP、input_max_len↔attn-TP）。上多卡 EP / 序列并行前，输入维度（global batch、序列长）必须对齐到并行度——否则启动即 raise ValueError，或序列维在各 rank 上切不均。换新模型/新卡数时先核这几处约束。Ulysses 按 head 切分的整除约束是另一族，见 ulysses-head-seq-divisibility-uaa。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.speculative_decoding
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/4
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/193
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 多卡 MoE/SP 部署的整除·对齐约束（batch↔EP、input_max_len↔attn-TP）

## 适用场景

上多卡 [EP](../../concepts/parallelism/expert_parallel.md) / 序列并行前，输入维度（global batch、序列长）必须对齐到并行度——否则启动即 `raise ValueError`，或序列维在各 rank 上切不均。换新模型/新卡数时先核这几处约束。Ulysses 按 head 切分的整除约束是另一族，见 [ulysses-head-seq-divisibility-uaa](ulysses_head_seq_divisibility_uaa.md)。

## 约束一：EP 部署 global batch_size 必须被 moe_ep_size 整除

**信号**：启动阶段抛 `ValueError: batch_size=<n> is not divisible by moe_ep_size=<m>`。

**触发/根因**：`moe_ep_size = world_size // moe_tp_size`；MoE EP 把 global batch 均分到各 EP rank（`batch_size_per_rank = batch_size // dp_size`，EP 路径同理），不整除则 token 无法均匀分派到专家分组。启动前 `check_parallel_settings` 直接校验 `batch_size % moe_ep_size != 0` 抛错。

**修法**：把 global `batch_size` 设为 `moe_ep_size` 的整数倍（EP 全量时即 `world_size // moe_tp_size` 的倍数）。样例佐证：`world_size=16, moe_tp_size=1 → ep=16` 用 `batch_size=16`；`moe_tp_size=16 → ep=1` 用 `batch_size=1`。相关：`exe_mode ∈ {ge_graph, eager, acl_graph}`（否则 `raise`），`acl_graph` 下 `TASK_QUEUE_ENABLE` 被强制为 1。

## 约束二：SP prefill 的 input_max_len 必须对齐到 attn_tp（并给 MTP 预留位置）

**触发条件**：MoE 大模型 prefill 同时开 attention [TP](../../concepts/parallelism/tensor_parallel.md) 与 MoE EP（`attn_tp_size > 1 and moe_ep_size > 1`），即启用 [SP 序列切分](../../concepts/parallelism/sp_tp_sp.md)——序列维会沿 attn TP 各 rank 切分。

**根因/修法**：
1. **对齐**：`input_max_len = align_up(input_max_len, attn_tp_size)`——序列维若非 `attn_tp_size` 整数倍，无法在各 attn TP rank 均匀切分。
2. **总长重算给 MTP 预留**：`max_position_embeddings = max_new_tokens * (next_n + 1) + input_max_len`。`(next_n + 1)` 是 [MTP 推测解码](../../concepts/techniques/mtp_speculative_decoding.md)"推测 token 全部被接受"的吐出上界（每步额外 `next_n` 个加自身 1）；仅按 `align_up(max_position_embeddings, pa_block_size)` 定总长会在 SP+MTP 组合下留下位置不足隐患。

```python
if attn_tp_size > 1 and moe_ep_size > 1:      # SP 激活
    input_max_len = align_up(input_max_len, attn_tp_size)
    max_position_embeddings = max_new_tokens * (next_n + 1) + input_max_len
```

## 适用边界

约束一证据覆盖 [Qwen3-MoE](../../concepts/models/qwen3_moe.md) 启动校验；约束二覆盖 [DeepSeek-R1](../../concepts/models/deepseek_r1.md) 建模文件（`model_setting.py`）。两条为本仓该几个建模文件的 config/启动约束，未升为整个昇腾栈通用律；但"EP 要求 batch 整除 ep_size、SP prefill 要求序列长对齐 attn_tp"这一判断对同类 MoE/SP 多卡部署可迁移。约束二有评审建议"对齐是否应与 cp_size 而非 attn_tp_size 相关"，合入版仍按 `attn_tp_size`。

## Evidence

- `diff 事实`（@e8eb6979，约束一）：`check_parallel_settings` 的 `batch_size % moe_ep_size` 断言 + 5 份 config YAML 的 batch/ep 组合自洽。溯源下探：[cann-recipes-infer-pr-4-qwen3moe](https://gitcode.com/cann/cann-recipes-infer/merge_requests/4)
- `diff 事实` + `维护者确认`（@355e29ed，约束二）：`model_setting.py::update_vars` 新增 SP 分支的 `align_up` + `max_position_embeddings` 公式；SP 判定条件与 `(next_n+1)` 语义由作者确认。溯源下探：[cann-recipes-infer-pr-193-fix-max-input-len](https://gitcode.com/cann/cann-recipes-infer/merge_requests/193)