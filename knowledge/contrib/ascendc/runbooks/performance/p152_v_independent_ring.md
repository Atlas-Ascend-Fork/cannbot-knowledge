---
type: Runbook
title: "P152 Playbook: 把 V 从共享 L1 页槽拆成独立环，并在 PV 头部预取 落地 SOP"
description: "完整发现记录见 ../../optimizations/evolution_strategies/discovered/disc_x144.md。"
tags:
  - task.optimization
  - topic.attention
  - topic.memory
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/discovered/disc_x144.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p152_v_independent_ring.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/1084df8aaa86b2e7a0ca4e723b4ea4b366cd3eeb/community/ops/ascendc-evolution-strategies/references/preconditions/P152.yaml
    role: constraint
created_at: "2026-11-03T15:14:30Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
aliases:
  - P152
---
# P152 Playbook: 把 V 从共享 L1 页槽拆成独立环，并在 PV 头部预取 落地 SOP

> 证据状态：结构化来源为对应 X 发现记录（固定 commit）；实际算子的正确性/性能验证报告尚待补充。补齐前请把本卡视为待验证晋升，不用于强结论。

> 强制流程。完整发现记录见 [../../optimizations/evolution_strategies/discovered/disc_x144.md](../../optimizations/evolution_strategies/discovered/disc_x144.md)。

## Step 1: 取证

```bash
grep -nE "PhasePV|M_MTE2|V" op_kernel/*.cpp op_kernel/*.h op_host/*.cpp op_host/*.h 2>/dev/null | head -50
```


## 背景与判定
MIX(CV) 注意力环里，AIC 相位顺序是 `QK(m)` → `PV(m-1)`，K 与 V 共用同一批 L1 页槽。于是 `PhasePVGrp` 开头必须做一次**全排空**（`SetFlag/WaitFlag<HardEvent::M_MTE2>`：等所有 QK gemm 退役，页槽才能改作 V 用），而 PV 之后还要**重新发一遍 V 页 DMA**——两次都是纯串行化。

本机制分四步：

1. **V 独立环**：设置 `kVSplit`（按 PAIR/D 档位门控），给 V 分配专用槽，放在 K 环与 P 环之间。K 环槽数相应减少，L1 总量保持不变，用 `static_assert(kL1Use <= L1_BUDGET)` 守住。
2. **在 PV 头部预取**：`PhasePVGrp` 一进来（**在 `CrossCoreWaitFlag` 之前**）就为该 pair 的前几组发 V 页 DMA。这里通常是 AIC 等 AIV softmax 的空闲窗口，预取不额外占用关键路径。
3. **删掉 M_MTE2 全排空**：V 环与 K 环物理分离，QK 的 gemm 不再需要先让出 L1。
4. **P 环解耦**：issue-ahead 的瓶颈常在 P 环而不是 K 环；`kPP = kVSlot` 让 PV 有足够的提前量。PV 的事件 id 要换成 group 信号量（如 `i & 1`），否则仅有的两个 MTE2_MTE1 id 在"两组在飞"时无法保持 Set/Wait 严格交替。

## 适用场景
- 只在 AIC 相位顺序为 `QK(m) → PV(m-1)` 且 K/V 共槽的结构下成立（这是多数 CV 环注意力的形态）。
- L1 必须有余量放独立 V 环：`extra_L1 = V_slot_bytes * V_slots`。D 较大时 V slot 很大，同结构可能装不下，应走别的路（例如 X145 的 L0B 双槽）。
- 单条 V 环槽数 = 预取深度 + 1；每增加一级预取都要重新验证 L1 预算与目标 shape。

## Step 2: 实施
1. **预取位置不能放在 QK 阶段**：AIC 先跑 QK(m) 再 PV(m-1)；QK 期填的 V 环装的是 pair m 的页，`PV(m-1)` 会把它们当自己的 V 覆盖掉，造成静默错值。正确位置是 `PhasePVGrp` 头部、`CrossCoreWaitFlag` 之前：同一个空闲窗口，几条指令之差，但可证明属于正确的 pair。
2. 把 `MakeCtx` 提到 wait 之前是安全的：纯索引算术，无副作用。
3. **issue-ahead 的真瓶颈可能是 P 环**：只拆 K/V 环而不解耦 P 环，PV 只能提前一组；P 环槽数与事件 id 必须一起调整。
4. 每个被删除的排空都要证明其 RAW/WAR 已被其他 flag 覆盖；不要凭"看起来冗余"直接删。
5. V 环的槽信用要与 K 环分开计数，避免 id 撞车。

## Step 4: 边界与回退
- 若 D 较大、V slot 超预算，独立环不成立；不要强行缩 slot 到影响 DMA burst。
- 本机制的理由是"空闲窗口免费预取 + 删掉全排空"，不是"消除第二次读"。若 K/V 已经是两块连续平面，K 的读不会把 V 带进 L1，收益应重新核算。

## Step 3: 验证
- 对每个 pair 检查预取的 V 页确实属于该 pair；用毒化/哨兵值验证没有跨 pair 覆盖。
- 同设备同窗口 A/B；重点看 M_MTE2 全排空是否消失、PV 启动是否提前。
- 精度：全量 case + 尾块、非整除、不同 D 档。

## 关联
- 与 [X145](../../optimizations/evolution_strategies/discovered/disc_x145.md)（L0B 双槽）正交，可叠加；两者都从"减少 DMA 与 mma 的串行化"入手。
- 与 [X128](../../optimizations/evolution_strategies/discovered/disc_x128.md)（槽信用时序）共享"上一读者决定发车点"的分析方法。
