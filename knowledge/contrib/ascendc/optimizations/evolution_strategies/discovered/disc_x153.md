---
type: Optimization
title: "X153: MLA/GQA decode 的 head_block 惩罚主要来自 cube FLOPs，不是 AIV"
description: "在 MLA/GQA decode（kvHeads=1、矩阵吸收）中，QK/PV 的 M 轴正比于 head_block，而 KV 字节不变；因此增大 head_block 会按倍数增加 cube FLOPs，形成结构性 per-chunk 惩罚。做受控对照（同 B、同 KV、同发布字节、同每核迭代数）可把该惩罚与 AIV 侧成本分开；AIV 侧改造的上限通常很小。"
tags:
  - task.optimization
  - topic.attention
  - topic.parallelism
status: draft
sources: []
created_at: "2026-10-28T15:00:00Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X153: MLA/GQA decode 的 head_block 惩罚主要来自 cube FLOPs，不是 AIV

## 核心思路
在 MLA/GQA decode（kvHeads=1、矩阵吸收、V 复用 K 的列）中，QK 与 PV 的 M 轴正比于 `head_block`，而 KV 的字节量由 KV 长度与 head_dim 决定，**不随 head_block 变化**。因此增大 `head_block` 会按倍数增加 cube FLOPs：

- QK: `[hb, dqk] × [dqk, TOK]`
- PV: `[hb, TOK] × [TOK, dc]`

两式的 M 轴都是 `hb`。这会形成一个结构性的 per-chunk 惩罚，与 AIV 侧 online-softmax/rescale 的成本无关。

## 适用场景
MLA/GQA decode（kvHeads=1、矩阵吸收、V 复用 K 的列）中，head_block 增大后需要判断 per-chunk 成本主要来自 cube FLOPs 还是 AIV 侧时。

## 受控对照方法
要判断某档 shape 的 per-chunk 成本主要花在哪里，做"同 B、同 KV、同发布字节、同每核迭代数"的对照：

1. 选两个 shape，只改变 `head_block`（一个较大、一个较小），其它条件尽量一致。
2. 确认两者的 AIC MTE2 发布字节数与每核 chunk 迭代数相同；若不同，先归一化到 per-chunk。
3. 按目标核的 cube 峰值折算 QK/PV 的 FLOPs 增量，得到 cube 侧理论差。
4. 剩余差值归入 AIV 向量侧（V1 online-softmax、V2 rescale 等）。

若 cube 侧理论差已经能解释大部分实测差，则 AIV 侧的可优化空间很小；反之才值得投入 AIV 改造。

## 结论与边界
- AIV 侧的能量上限通常远小于 cube 侧的结构性差异；"head_block 大所以 AIV 慢"是常见误判。
- **hb 很大时不要指望 nomax + acc_o 常驻 L0C**：`hb * dc * 4` 可能单块就占满 L0C，放不下 acc_s。先做容量审计（见 X126/X149）。
- H 很大时，"双 hgroup 折叠"也不一定有靶子：若两次读的发布字节与每核迭代数相等，第二次读已经和第一次一样快（L2 时序天然吃到），折叠没有收益且 UB/L0C 放不下。
- 本卡适用于 MQA/GQA/MLA decode 这类 M 轴 ∝ head_block 的结构；prefill 或 M 轴为 query 行数的结构需重新分析。

## 验证方法
- 用受控对照（只改 head_block）验证 per-chunk 成本差。
- 按目标核峰值折算 FLOPs；不要用整机峰值，也不要用未校准的标称值。
- 对 AIV 侧候选改造做同窗口 A/B；若 cube 侧已解释大部分差异，AIV 改造的预期上限应设得很低。
- 精度与 KV 口径：确认 V 的复用关系（V 是否等于 K 的前 dc 列）在对照中保持一致。

## 关联
- 与 [X172](disc_x172.md)（MLA decode 分档）配合：先分档，再判断 head_block 惩罚的来源。
- 与 [X126](disc_x126.md)、[X149](disc_x149.md) 共享 L0C 容量约束。
