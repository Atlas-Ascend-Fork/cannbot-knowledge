---
type: Optimization
title: 'F6: P4+P140+P142:attention:dc-split-doubles-gather'
description: P4+P140+P142:attention:dc-split-doubles-gather (performance_negative)
tags:
- task.debugging
- topic.data_movement
- topic.kv_cache
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/4917980395de8b8703aa7ec62213fafbe7bec01e/plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/runbooks/failure-patterns/f6-dc-split-doubles-kv-gather.md
  role: evidence
created_at: '2026-10-30T11:40:00Z'
updated_at: '2026-10-30T11:40:00Z'
platforms:
- a2
- a3
---

# F6: P4+P140+P142:attention:dc-split-doubles-gather

> 进化失败模式元数据（迁移自旧 OKF，机器可读副本见 ascendc-evolution-knowledge/references/okf_compat.json）：
> key: "P4+P140+P142:attention:dc-split-doubles-gather"
> phenomenon: performance_negative
> severity: major
> failed_combination: ["P4", "P140", "P142"]
> operator_type: ["attention", "flash_attention", "mla"]
> occurrences: 1

## f6: 把 dc 维对半拆到两个核（每核一半列）→ KV gather 体积翻倍，负收益

## 现象
MLA decode（paged KV）里 hb=64（H=64/H=128）路径因 L0C 128KB 放不下
`acc_o(64x512x4=128KB) + acc_s(24.6KB)` 而退回 running-max（每 chunk 落 ws_o）。
为了「让 nomax 复活、消掉 ws_o」，把 dc 维对半拆到 2 个核（每核 acc_o=65,536B + acc_s=24,576B
= 90,112B ≤ 128KB），两半核各自做完整 gather+QK。

## 症状（实测）
- 被治 8 例组内几何 **+27.7%**：c36 +34.9%、c49 +82.9%、c25 +28.5%、c11 +25.4%、c14 +22.3%、
  c30 +19.7%、c8 +16.5%、c23 +3.9%；全量 327.96 → 339.35us（+3.47%）；精度 50/50 通过。
- 非目标 42 例 |Δ| ≤ 2%（说明不是环境噪声）。

## 根因类别
**每核 AIC MTE2 的 gather 有效带宽是硬墙，且与 L2 命中无关**：
- 每核 gather 有效带宽实测 24.6~34.5 GB/s（110,592B/chunk ÷ 4.5~3.2us），与「是否已被 AIV 预热带进 L2」
  基本无关；因此**复制 gather 体积 = 线性变差**，指望「第二份读命中 L2」不成立。
- 反证：ws_o ring 只有 6.3MB 且常驻 L2，**不是 HBM 流量** —— 原「每 chunk 128KB ws_o 写读把 DRAM 推过峰值」
  的假设是错的；ws_o 不是瓶颈。

## Resolution
1. 不要用「多核复制同一个 page-range」（dc/head 拆分、多一份 gather）去换 L0C 空间；
   要么减少 gather，要么压缩「chunk 内未掩盖的串行段」（本算子约 1.56us/chunk）。
2. 想要 nomax 的 L0C 空间，优先考虑**单核内**的行/列分片 + 分组累积（组内共享 m0，组末才 flush），
   而不是增加一份 KV 读。
3. 判定任何「拆维换并行」的提案前，先量化 `每核 gather GB/s` 与 gather 体积倍数。

## 证据
53_BatchDecodeMlaPaged round_1/parallel_0（node n2，dc 对半双核切分）：certified 50/50、
14.493x / 339.35us；implementation_note.txt 含逐 case 表与机理。
