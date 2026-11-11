---
type: Optimization
title: "双链单指令打包（PCP — Paired-Chain Packing）：把两条保序顺序归约链合并进一条 2-repeat 向量指令"
description: "当 kernel 里存在两条结构相同、互不依赖、都必须保序的顺序归约链（同一面板上同时算两条 p 升序的 rows 次 1-repeat Add），关键路径长度 = 链长 rows；把两条链合并进同一条 2-repeat 向量指令可将指令数减半且数值逐位不变，前提是源数据落在同一行内固定步长位置。"
tags:
  - task.optimization
  - topic.data_movement.layout_transform
  - topic.compute.reduction
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X79: 双链单指令打包（PCP）

## 核心思路

当 kernel 里存在**两条结构相同、互不依赖、都必须保序**的顺序归约链
（典型：同一面板上同时算两条 p 升序的 `rows` 次 1-repeat `Add`），关键路径长度 = 链长 `rows`，
且**改结合序会破坏低精度输出**——此时不能换折半树。

X79 的做法：把两条链**合并进同一条 2-repeat 向量指令** ——
`repeat0` 推链 A、`repeat1` 推链 B，每条链自身仍是「p 升序、每步一次加法」，**数值逐位不变**，
但指令数从 `2·rows` 降到 `rows`（关键路径减半）。

前提是两条链的**源数据必须落在同一行内的固定步长位置**：因此需要把 UB 布局从
「三块独立缓冲」改为**行内三组 `[S_a | S_b | T]`**（同行的 a/b/t 相距固定 stride），
2-repeat 才能用一对 (src0RepStride, src1RepStride) 同时表达两条链的推进。

## 适用场景

- 逐 token / 逐 step 的向量核里，一个面板/一个 token 上同时要算 ≥2 条**独立的、保序的**列归约；
- 两条链的迭代次数相同（同为 `rows`）、且能改造成行内固定步长布局；
- 低精度（bf16/fp16）输出导致**不能换结合序**的场景（这是 X79 相对「折半树」的独占价值）。

## 实现要点 / 红线

- **绝不能变成 `2·rows` 条独立指令**：那样只是把循环合并，链长不变，不带来收益。
- 2-repeat 的两条链必须**独立无依赖**；若共享累加器则退化为串行。
- 行内布局改造会改变所有消费该缓冲的面板代码（stride/offset 全面重算），
  **UB 预算公式要一起更新**；改造后必须逐用例复核（曾因删除预块骨架导致主循环前若干面板
  读到陈旧缓冲，多个输出全错）。
- 保序性必须以固定种子的参考输入逐元素确认（worst MARE 应与父内核**逐位相同**，而不是「恰好过」）。

## 边界

- 反例 1：把一条归约链摘成独立 kernel，虽然减少 pass，但多一次 launch 与状态张量重读，净收益为负。
- 反例 2：折半树改序虽可加速，但会破坏 bf16 输出精度。

## 验证方法
- **性能**：在目标设备上对父变体与变体做同一时间窗口的 A/B（正反序至少两轮），
  以绝对时延和配对差值判断，不用跨窗口比值。
- **精度**：跑全量精度用例，用固定种子参考输入逐元素对比父内核；保序路径要求 worst MARE
  逐位相同。
- **容量**：行内布局改造后重新审计 UB 预算（stride/offset 与组缓冲），确认无越界或陈旧读。
