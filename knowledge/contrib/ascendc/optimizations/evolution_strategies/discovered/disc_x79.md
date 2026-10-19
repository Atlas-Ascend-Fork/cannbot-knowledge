---
type: Optimization
title: "双链单指令打包（PCP — Paired-Chain Packing）：把两条保序顺序归约链合并进一条 2-repeat 向量指令"
description: "当 kernel 里存在两条结构相同、互不依赖、都必须保序的顺序归约链（典型：同一面板上同时算 dC = Σ_p tile_a[p] 与 dB = Σ_p tile_b[p]，都是 p 升序的 rows 次 1-repeatAdd），关键路径长度 = 链长 rows（本算子 rows = PP ≤ …"
tags:
  - task.optimization
  - topic.data_movement.layout_transform
  - topic.compute.reduction
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X79: 双链单指令打包（PCP）

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X79
> title: "双链单指令打包（PCP — Paired-Chain Packing）：把两条保序顺序归约链合并进一条 2-repeat 向量指令"
> origin: discovered
> discovered_round: 3
> discovered_from: "Mamba2Bwd evolution, round_3/parallel_2 (node x0_r2a_r3o, open_exploration)"
> base_speedup: "同窗 A/B 1.158x（父内核 675.23us -> 582.81us）；父内核 22.31x -> 25.79x vs PyTorch"
> confidence: single_op
> status: active
> op_families: [ssm, chunk-scan, recurrent, reduction]
> bottlenecks: [scalar_compute, sync_overhead, no_overlap, instruction_sched]
> tags: [paired-chain, 2-repeat, reduction-chain, order-preserving, panel-layout, ub-layout, critical-path, mamba2bwd, 910b2c, dav-c220]
> strategy_ids: [X79, X78, P94]
> ```

## 核心思路

当 kernel 里存在**两条结构相同、互不依赖、都必须保序**的顺序归约链
（典型：同一面板上同时算 `dC = Σ_p tile_a[p]` 与 `dB = Σ_p tile_b[p]`，都是 p 升序的 `rows` 次 1-repeat
`Add`），关键路径长度 = 链长 `rows`（本算子 rows = PP ≤ 128），且**改结合序会破坏低精度输出**
（见 failure pattern f19）——此时不能换折半树。

X79 的做法：把两条链**合并进同一条 2-repeat 向量指令** ——
`repeat0` 推链 A、`repeat1` 推链 B，每条链自身仍是「p 升序、每步一次加法」，**数值逐位不变**，
但指令数从 `2·rows` 降到 `rows`（关键路径减半）。

前提是两条链的**源数据必须落在同一行内的固定步长位置**：因此需要把 UB 布局从
「SP0/SP1/TPb 三块独立缓冲」改为**行内三组 `[S_a | S_b | T]`**（同行的 a/b/t 相距固定 stride），
2-repeat 才能用一对 (src0RepStride, src1RepStride) 同时表达两条链的推进。

## 适用场景

- 逐 token / 逐 step 的向量核里，一个面板/一个 token 上同时要算 ≥2 条**独立的、保序的**列归约；
- 两条链的迭代次数相同（同为 `rows`）、且能改造成行内固定步长布局；
- 低精度（bf16/fp16）输出导致**不能换结合序**的场景（这是 X79 相对「折半树」的独占价值）。

## 实现要点 / 红线

- **绝不能变成 `2·rows` 条独立指令**：那样只是把循环合并，链长不变（同轮实测 v6a 交错版 = 1.0000x，
  是这条红线的反例）。
- 2-repeat 的两条链必须**独立无依赖**；若共享累加器则退化为串行。
- 行内布局改造会改变所有消费该缓冲的面板代码（stride/offset 全面重算），
  **UB 预算公式要一起更新**；改造后必须逐 case 复核（本算子曾因整段删除预块骨架导致主循环前 npan
  个面板读到陈旧 SP 缓冲 → ddt/dA/ddt_bias 全错）。
- 保序性必须用官方 seeded draw 实测确认（worst MARE 应与父内核**逐位相同**，而不是「恰好过」）。

## 来源

Mamba2Bwd evolution（进化基线）round_3/parallel_2（node x0_r2a_r3o, open_exploration）；
同轮已验证的**反例**：把 dC 摘成独立 kernel（少 2/11 pass）因多一次 launch + S_all 重读 1.4GB
净亏损 1.135x（见 OKF failure pattern `P102:kernel-split:dc-hoist-sall-reread-floor`）；
round_2 的 ICRD（折半树改序）1.402x 但破坏 bf16 dB（failure pattern f19）。
