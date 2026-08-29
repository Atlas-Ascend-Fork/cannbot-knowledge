---
type: Optimization
title: 稀疏/反量化 Attention 走非 Page-Attention 路径时 Q 与 KV 必须同布局（不一致 → host tiling GRAPH_FAILED）
description: 稀疏/反量化 Attention 走非 Page-Attention 路径时 Q 与 KV 必须同布局（不一致 → host tiling GRAPH_FAILED）。给稀疏/反量化 attention 算子配置非 Page-Attention 路径（连续 BSND 或变长 TND 的 KV，而非分页 PA_BSND）时，图编译/tiling 阶段直接挂掉、host tiling 返回 ge::GRAPH_FAILED，还没进 kernel。典型触发是 Q 与 KV 布局不一致——例如 layoutQ=BSND 配 layoutKV=TND，或 layoutQ=TND 配非 PA_BSND 的 KV。这不是运行时精度问题，是 host 校验阶段的硬约束。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/60
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 稀疏/反量化 Attention 走非 Page-Attention 路径时 Q 与 KV 必须同布局（不一致 → host tiling GRAPH_FAILED）

## 适用场景

给稀疏/反量化 attention 算子配置**非 Page-Attention 路径**（连续 `BSND` 或变长 `TND` 的 KV，而非分页 `PA_BSND`）时，图编译/tiling 阶段直接挂掉、host tiling 返回 `ge::GRAPH_FAILED`，还没进 kernel。典型触发是 **Q 与 KV 布局不一致**——例如 `layoutQ=BSND` 配 `layoutKV=TND`，或 `layoutQ=TND` 配非 `PA_BSND` 的 KV。这不是运行时精度问题，是 host 校验阶段的硬约束。

## 条件 → 优先做什么

上非 PA 路径前先对照这份布局清单（host tiling 当前接受/拒绝的组合）：

- **Q/KV 布局一致性**：`kvLayout != PA_BSND` 时**强制 `qLayout == kvLayout`**。想用连续/变长 KV（`BSND`/`TND`）就必须让 Q 走**同一**布局；混搭（Q 与 KV 布局不同）**只在 `PA_BSND` 下合法**——分页 KV 走 block-table 间接寻址、与 Q 布局解耦，故允许 Q(`BSND`/`TND`) 与 KV 布局不同。违反会报「When layoutKV is not PA_BSND, layoutKV must be the same as layoutQ.」并返回 `ge::GRAPH_FAILED`。
- **key 维数**：key tensor 允许 3 维（`TND`）或 4 维（`BSND`/`PA_BSND`）；只按 4 维组织会拒掉 `TND` 输入。用变长 `TND` 时 key 要按 3 维组织。
- **s2Size 取轴**（batch-continuous 分支）：`BSND` 按 S 轴取 s2Size、`TND` 按 T 轴取；这两者之外的布局在该分支不成立。

**反例边界**：唯一允许 Q/KV 布局不同的是 `PA_BSND`（分页）。所以若确实需要 Q、KV 用不同布局，走分页 KV；否则统一布局。

## 问题信号 → 根因 → 修法

- **信号**：图编译/tiling 阶段直接失败，host tiling 返回 `GRAPH_FAILED`；不进 kernel、无运行时精度异常。
- **根因**：非 `PA_BSND` 路径下 Q 与 KV 布局不一致，被 host tiling 的布局一致性校验拒绝（或 `TND` 输入按 4 维 key 组织、被维数校验拒绝）。
- **修法**：连续/变长 KV 路径下让 Q 与 KV 同布局；`TND` 输入按 3 维 key、s2 沿 T 轴；需要 Q/KV 异布局则改走 `PA_BSND` 分页 KV。

## 参考实现及其约束

约束落在本仓 SFAA 算子（`sparse_flash_attention_antiquant`，[sparse-flash-attention](../../../concepts/kernels/sparse_flash_attention.md) 的 antiquant 变体，AscendC 实现）的 host 侧 tiling（`op_host/sparse_flash_attention_antiquant_tiling.cpp`，解析类 `SFAAInfoParser` / 校验类 `SFAATilingCheck`）：`GetKvLayout` 的 `kvLayout != PA_BSND ⇒ qLayout == kvLayout`、`CheckSingleParaKey` 的 `{3,4}` 维数列表、`GetS2SizeForBatchContinuous` 的 `TND` 按 T 轴分支。这些是**该算子 host 校验当前接受/拒绝哪些布局组合**的事实，属该参考实现的约束、非对下游算子合约或整个昇腾栈的外推。

## 相关

- 同为「attention 算子输入契约随配置/后端不同、传错就在下发前失败」的姊妹经验：[fia-actual-seq-lengths-kv-backend-type](../../../runbooks/runtime/fia_actual_seq_lengths_kv_backend_type.md)（FIA 的 `actual_seq_lengths_kv` 类型随后端 host list / Tensor 之别）。
- 走 AscendC 后端的选型背景：[op-backend-selection-ascendc-pypto-tilelang](op_backend_selection_ascendc_pypto_tilelang.md)。
- 概念页：[sparse-flash-attention](../../../concepts/kernels/sparse_flash_attention.md) · [ascendc](../../../concepts/frameworks/ascendc.md)。

## 相关经验
- [FIA/qlens 的 block_table 首维 / num_reqs / TND se](../../../runbooks/runtime/fia_qlens_block_table_num_reqs_batch_contract.md)

## Evidence

- `diff 事实`（cann-recipes-infer，`@b9058045ec2d`）：host tiling 三处校验（`GetKvLayout` 的 `kvLayout != PA_BSND && qLayout != kvLayout` 约束与错误文案、`CheckSingleParaKey` 的 `{3,4}` 维数列表、`GetS2SizeForBatchContinuous` 的 `TND` 按 T 轴分支）均在合入代码中逐条对上；PR 已 merged，满足「代码 accept = 读过实际 diff」。
- 边界：适用面按证据限定到本仓 SFAA 算子（`sparse_flash_attention_antiquant`），未升为整个昇腾栈通用律；陈述的是 host 校验当前接受/拒绝的布局组合（有校验代码支撑），非对算子合约的外推。源未给性能/精度数字。
- 溯源下探：[cann-recipes-infer-pr-60-feat-sparse-flash-attention-antiquant-pa](https://gitcode.com/cann/cann-recipes-infer/merge_requests/60)。

<!-- cannbot:related:start -->
## 相关

- [Sparse Flash Attention Kernel](../../../concepts/kernels/sparse_flash_attention.md)（`related`）：约束落在本仓 SFAA 算子（`sparse_flash_attention_antiquant`，［sparse-flash-attention］(../../../concepts/kernels/sparse_flash_attention.md) 的 antiquant 变体，AscendC 实现）的 host 侧 tiling（`op_host/sparse_flash_attention_antiquant_tiling.cpp`，解析类 `SFAAInfoParser` / 校验类 `SFAATilingCheck`）：；`SparseFlashAttention` 是 DeepSeek-V3.2-Exp **DSA** 的主 Attention 算子 —— 在 ［lightning-indexer］(lightning_indexer.md) 产出的 TopK index 基础上，`Gather` 出稀疏 KV 子集并执行 Flash Attention 计算。。规则明确把受布局校验约束的 SFAA 标为 SparseFlashAttention 的 antiquant 变体，Kernel 卡则定义该稀疏注意力主算子的计算对象，二者共同界定变体的 host 布局入口与上层算子语义。
<!-- cannbot:related:end -->
