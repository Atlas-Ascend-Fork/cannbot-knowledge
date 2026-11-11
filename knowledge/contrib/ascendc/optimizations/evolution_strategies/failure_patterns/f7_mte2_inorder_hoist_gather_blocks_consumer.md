---
type: Optimization
title: 'F7: P61+P125:attention:mte2-inorder-hoist-gather-blocks-c2'
description: P61+P125:attention:mte2-inorder-hoist-gather-blocks-c2 (performance_negative)
tags:
- task.debugging
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/4917980395de8b8703aa7ec62213fafbe7bec01e/plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/runbooks/failure-patterns/f7-mte2-inorder-hoist-gather-blocks-consumer.md
  role: evidence
created_at: '2026-10-30T12:30:00Z'
updated_at: '2026-10-30T12:30:00Z'
platforms:
- a2
- a3
---

# F7: P61+P125:attention:mte2-inorder-hoist-gather-blocks-c2

> 进化失败模式元数据（迁移自旧 OKF，机器可读副本见 ascendc-evolution-knowledge/references/okf_compat.json）：
> key: "P61+P125:attention:mte2-inorder-hoist-gather-blocks-c2"
> phenomenon: performance_negative
> severity: major
> failed_combination: ["P61", "P125"]
> operator_type: ["attention", "flash_attention", "mla"]
> occurrences: 1

## f7: 把长 gather 前移到迭代头 → MTE2 按序队列挡住下游小载入，+5~+11%

## 现象
MLA decode（paged KV，k_slots=4，hb<=32）里为提高 gather 的 MLP，把 chunk t+1 的
6×18,432B page-gather 从 C1 内部**前移到迭代头**（在 C2(t-2) 的 P/P_lo 载入之前发车）。

## 症状（实测）
- k_slots=4（hb<=32）**集体 +5~+11%**：c26 +9.9、c31 +10.0、c44 +10.3、c29 +8.8、c27 +8.3、
  c40 +8.4、c35 +6.6、c15 +6.2、c48 +5.3；k_slots=3（hb=64，仅吃到中性重排）只 +1.6~+2.6%。
- 全量 certify：338.51us vs 起点 322.23us（+5.3%），精度 50/50 通过。
- 剂量-响应沿 k_slots 边界分层 ⇒ 不是窗口噪声。

## 根因类别
**MTE2 是同核按序队列**：长 gather 排在 C2(t-2) 的 P/P_lo（2×6,144B）之前，使 C2 的 mma 晚一整个
gather（~1.5us）；而 C2 完成又门控下一迭代的 K 槽信用与 SIG_O_READY，于是整条依赖链被拉长。
附带实测：aic_mte2 只有 0.61 ⇒ gather 不是带宽墙（每核可用 ~51 GB/s），第一管道是 scalar 0.88。

## Resolution
1. 提前发车必须按**同队列在序**判断：谁在 MTE2 队列里靠前，谁先完成。小载入（P/P_lo）应排在长 gather 之前。
2. 正确方向是「**C2 供数优先**」：迭代头先发 C2 的 P/P_lo 与 V 载入，让 C2 的 mma 尽早开跑；gather 排其后。
3. 要真正提高 gather MLP，需要**更多 K 槽**（L1 预算允许时）或降低 TOK/分块 dim_align，而不是重排已有槽。

## 证据
53_BatchDecodeMlaPaged round_2/parallel_0（node n2_cont）certified 14.529x / 338.51us；
implementation_note.txt 含剂量-响应表与 k_slots 分层证据。
