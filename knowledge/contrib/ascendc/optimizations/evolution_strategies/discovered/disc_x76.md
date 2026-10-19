---
type: Optimization
title: "分组相位化调度（grouped phase-split）：每核 G 块一组、G×MTE2 → G×VEC → G×MTE3，打破同序发射下的 per-tile DMA 往返暴露"
description: "AIV 是同序发射核：程序里先 DeQue 拿到 WaitFlag(MTE2→V)，标量才会继续发射下一条指令。"
tags:
  - task.optimization
  - topic.implementation.synchronization
  - topic.data_movement
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# X76: 分组相位化调度（grouped phase-split）

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X76
> title: "分组相位化调度（grouped phase-split）：每核 G 块一组、G×MTE2 → G×VEC → G×MTE3，打破同序发射下的 per-tile DMA 往返暴露"
> origin: discovered
> discovered_round: 4
> discovered_from: "Exp evolution, round_4/parallel_2 (node x0_x1_x1_x1, open_exploration / DRIFT_REPLAN)"
> base_speedup: "[部分撤回] 首测 geomean 5.1171x -> 5.1891x；但 round-5 的同窗对照显示该内核逐字节相同地重测为 5.0454x（Σasc 859.2us）⇒ 首测值含 ~2.8% 窗内/争用膨胀，且 idx3 的 -20.6% 未复现（见「撤回」节）。当前可辩护的结论：与未改动的对照内核无显著差异（在 ±1.5~3% 噪声带内）。"
> confidence: single_op
> status: active
> op_families: [elementwise, broadcast]
> bottlenecks: [no_overlap, mte2_stall, mte3_stall]
> tags: [phase-split, grouped-schedule, dma-latency, in-order-issue, waitflag, elementwise, streaming, group-depth, 910b2c, dav-c220, l2-residency]
> strategy_ids: [X76, P1, P19, P20, P66]
> ```

> **[2026-09-11 部分撤回 — 请先读这一节]** 本卡的因果主张（idx3 因相位化 -20.6%）**未能复现**：
> round-5 用逐字节相同的 phase-split 内核重测，idx3 = 211.58us（另一变体 215.84/216.46），全部落在稳态 ~211-216us 带内。
> 同一内核的全量 geomean 也从 5.1891 变为 5.0454（Σasc 817.0 → 859.2us）。⇒ round-4 的 v1(171.42)/v2(214.94) 对比是**双模态快/慢采样**，不是因果。
> **保留价值**：相位化调度本身无害（20/20 bit-exact、UB/语义不变），但**其收益未被证实**；引用本卡时必须携带该撤回声明，且只能当作「待验证的调度形态」。
> 教训：单 case 的「因果」结论必须在**同一窗口内做 ≥2 次重复 + 未改动对照**才能成立（本环境单 case 双模态 + 跨窗漂移 ±2.8%）。

## 核心思路
AIV 是**同序发射**核：程序里先 `DeQue` 拿到 `WaitFlag(MTE2→V)`，标量才会继续发射下一条指令。
经典逐 tile 写法 `CopyIn → Compute → CopyOut` 因此让 **tile t+1 的 MTE2 必须等 tile t 的 VEC 完成才发射** —— 声明的 TQue 深度
（例如 xIn 3 深）根本没有被当作预取用，每个 tile 暴露一次完整的 DMA 往返（实测 per-tile ≈1.2us）。

**分组相位化**把每核的 tile 流按 G 块一组切成三个相位：

```
for each group of G tiles:
    相位 1: 发射 G 次 CopyIn (G×MTE2)          # 全部在飞
    相位 2: 发射 G 次 Compute (G×VEC)          # 与相位 1 的尾部重叠
    相位 3: 发射 G 次 CopyOut (G×MTE3)         # 与相位 2 的尾部重叠
```

UB 占用、队列深度声明、搬运量、tile→核映射、计算链**逐位不变** —— 只改主循环结构（本例只动了 `exp_kernel.h` 一个文件：
`Process` 主循环 + 新增 `ProcessGroup`/`ComputeInto`/`kGroup` static_assert）。

## 适用场景
- **算子类型**：elementwise / streaming 类（每 tile 独立的 CopyIn/Compute/CopyOut），AIV_ONLY 或 AIV 主导
- **前提**：每核 tile 数 ≥ 3（否则没有组可组，预期中性）；UB 能容纳 G 块同驻
- **瓶颈标签**：no_overlap / mte2_stall / mte3_stall
- **预期收益**：**未证实**（见顶部撤回节）。首测为全域 geomean +1.4%/Σasc -4.94%，但同内核重测回落至与未改动对照无显著差异。

## 实现要点
- **组深度 D 需要逐档标定，但本卡的「D=2 尖峰最优」证据已撤回**：首测显示 D=2 时 idx3=171.42us、D=3 回到 214.94us，
  但同内核重测 idx3 在 D=2 下也是 211-216us ⇒ 该对比是双模态采样。**仍建议按档试 D（2/3）并做同窗重复对照**，不要引用具体数字。
- 用**声明式 TQue 深度**表达预取，不要手写 prologue / 手工多标量预取
  （X23 记录过手写预取触发编译器误编译；X4 记录过 EnQue/DeQue 同步开销在小工作量上反客为主）。
- 组内每块仍各自 EnQue/DeQue，相位化只改**发射顺序**，不改同步语义；跨相位边界只保留必要的 `PipeBarrier<PIPE_V>`
  （本算子每 tile 只有 2 次必需 V 屏障，删不得 —— P30 的 PIPE_V 乱序语义陷阱）。
- `static_assert` 约束 G 与 UB 预算，避免编译期静默越界。
- 按档选择调度：light 档（1M-2M、每核 2±1 块）无组可组，应保留原串行循环，不要为了统一而强行分组。

## 边界 / 实测否定项
- [negation] **无条件 load-ahead / 加深预取**（同族但不同机制）：在另外两次独立尝试中分别表现为
  「L2 驻留中档 case -2.6~-5.0%，但 4-tile 短循环 +10.6~+21.6%、HBM 驻留 case +4.1%，净 +0.7% 低于噪声」
  与「把在飞 MTE2 请求数翻倍完全不改变 idx12 的带宽（20.46→20.54us）」⇒ 不是「多发请求」而是「按组三相位重排发射」才有效
- [negation] 组深度越大越好：多次观测显示 D 增大到 3 时大流式 case 更容易落回慢模态（但本环境双模态使该效应难以单次裁决）
- 本卡证据为 `single_op` 且**核心结论已部分撤回**；换算子时只能把它当「无害但收益未证实的调度形态」，并且**必须**用同窗未改动对照 + ≥2 次重复来裁决

## 来源
自动发现于 Exp 算子进化 round 4（node x0_x1_x1_x1 = round_4/parallel_2，open_exploration + DRIFT_REPLAN）。
首测全量 20 case geomean 5.1891x（20/20 精度，per-case `msprof --quick`、warm-up=2、device 3、持设备锁）；
**round-5 同窗重测该逐字节相同内核得 5.0454x（Σasc 859.2us）** ⇒ 首测值含 ~2.8% 窗内/争用膨胀。
idx3 的 171.42us 未被复现（重测 211.58/215.84/216.46us）⇒ 原「因果」结论撤回。
