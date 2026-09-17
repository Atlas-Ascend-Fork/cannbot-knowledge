---
type: Runbook
title: "`__CCE_AICORE__` macro values per Ascend arch (when reading CANN source)"
description: "`__CCE_AICORE__` is the bisheng compile-time arch macro. Common values seen in CANN source: - `100` = Ascend310 / 310p (older inference cards) - `200` = Ascend910 (original training) - `220` = **Ascen"
tags: [task.debugging, topic.compilation]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/bb96c9c595c7a8e96745d365291769dc48319c22/plugins-community/ascendc-port-orchestrator/kb/okf/runbooks/field-notes/build/ol-173-cce-aicore-macro-values-per-ascend-arch-when-readi.md
    role: primary
created_at: "2026-07-09T16:00:00Z"
updated_at: "2026-09-16T07:35:48Z"
platforms: [a3, "950"]
aliases: ["OL-173", "__CCE_AICORE__"]
---

# `__CCE_AICORE__` macro values per Ascend arch (when reading CANN source)

> 原 OKF v1 卡号：**OL-173**。
> 现象分类：build_failure；观测置信度：single_run（单次观测）。
> 触发信号：
> - encountering `#if __CCE_AICORE__ == NNN` in CANN kernel source

## 适用场景

- 适用技术与问题域：AscendC 编译/构建问题（现象分类：build_failure）。
- 适用平台：Atlas A2 系列、Atlas A3 系列、Ascend 950 系列；本卡为单次观测沉淀（single_run），按卡内声明范围消费。

## 教训 / 根因
`__CCE_AICORE__` is the bisheng compile-time arch macro. Common values seen in CANN source:
  - `100` = Ascend310 / 310p (older inference cards)
  - `200` = Ascend910 (original training)
  - `220` = **Ascend910b / Ascend910_93** (Atlas A2 / A3 — most CANN ops gated here)
  - `300` = (reserved / not seen in our context)
  - `350` = **Ascend950PR / Ascend950DT** (arch35 — our target A5)

## 证据
2026-04-24 op#3 — `cann/ops-nn/optim/advance_step/op_kernel/advance_step.cpp` has `#if __CCE_AICORE__ == 220` gate; no arch35 variant. The kernel uses PB-20 broken pattern → CANN explicitly excluded A5 from binary distribution. See OL-68 Case B.

<!-- 迁移自 porter OPERATIONAL_KNOWLEDGE.md OL-173（category=arch_compat，convert_ol_to_okf.py，M1）。confidence/severity/reproduce_count 未升格。 -->
