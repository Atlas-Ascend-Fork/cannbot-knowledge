---
type: Runbook
title: "P155 Playbook: softmax 两趟合成一条扁平 tile 流并提前 2 tile 预取 落地 SOP"
description: "完整发现记录见 ../../optimizations/evolution_strategies/discovered/disc_x156.md。"
tags:
  - task.optimization
  - topic.attention
  - topic.data_movement
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/discovered/disc_x156.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p155_softmax_flattened_tile_stream.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/1084df8aaa86b2e7a0ca4e723b4ea4b366cd3eeb/community/ops/ascendc-evolution-strategies/references/preconditions/P155.yaml
    role: constraint
created_at: "2026-11-03T15:14:30Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
aliases:
  - P155
---
# P155 Playbook: softmax 两趟合成一条扁平 tile 流并提前 2 tile 预取 落地 SOP

> 证据状态：结构化来源为对应 X 发现记录（固定 commit）；实际算子的正确性/性能验证报告尚待补充。补齐前请把本卡视为待验证晋升，不用于强结论。

> 强制流程。完整发现记录见 [../../optimizations/evolution_strategies/discovered/disc_x156.md](../../optimizations/evolution_strategies/discovered/disc_x156.md)。

## Step 1: 取证

```bash
grep -nE "softmax|Exp|rowmax" op_kernel/*.cpp op_kernel/*.h op_host/*.cpp op_host/*.h 2>/dev/null | head -50
```


## 背景与判定
CV 环的 softmax 通常写成两趟：**pass1 求整行全局 max**，**pass2 做 exp(−m)、行和、P 落盘**。两趟读同一批分数 tile，于是 tile 被 DMA 两遍，且每趟开头都有一次"空管启动"。

把它们看成**一条扁平流**：一个 item 的 `2*ngrp` 个 tile，
`tile q (< ng)` = pass1 的第 q 组，`tile q (>= ng)` = pass2 的第 `q-ng` 组，两者读同一个 ws1 地址。

- DMA **提前 2 个 tile** 发射（等 tile q 之后立刻发 q+2）→ 每个 tile 有两个迭代的落地时间。
- 环直接复用现成的 4 个分数槽（若 `GQA_NU * kScU == 4 * kSc2` 这类恒等式成立，UB 零增长；用 `static_assert` 守住）。
- 落地 flag 复用 `(q & 1)` 的两个 id：q 与 q+2 同奇偶 ⇒ 任一 id 都不会有第二个 outstanding set，不需要第三个 id。
- V→MTE2 drain 仍守着环槽（tile q+2 写的槽是 q-2 消费过的）。
- 正确性：pass1 的全局 max 必须先于 pass2 —— 扁平流的**顺序**（全部 pass1 tile 在前）天然保证。

## 为什么"减少工作量"可能没赚，"减少交付延迟"却大赚
同一类 CV 环上曾有探针证明：**直接删掉 pass1**（少一部分 S/P 字节、向量活减半）全集几乎不变。本机制**工作量几乎不变**（同样的 tile 读两遍）却能有明显收益。差别在：

- 删 pass1 减的是**吞吐代价**（而 AIV 侧本来可能大量空闲 → 不在关键路径）；
- 本机制缩短的是 **SC（分数就绪）→ P（P 就绪）的交付延迟**，而 P 是 cube 侧 PV gemm 的唯一前置。即使最大的 case 中 AIC MTE2 已接近饱和、L2 span 已到上限，PV 的启动时刻仍由 P 的到达决定。

**可复用判据**：CV 环里，"某相位在另一核的关键路径上"要看**交付延迟**，不要只看该相位的 pipe 占比。pipe 空闲不等于不在关键路径。

## Step 2: 实施（三处都是静默错值的坑）
1. 环槽复用前必须等**上一次消费**退役（V_MTE2 drain），否则 DMA 覆盖正在被读的槽。
2. flag 用 `(q & 1)` 而不是 `(q & 3)`：2-tile 提前量下，同奇偶的两次落地之间必有一次消费，才能保证"每 id 一个 outstanding set"。
3. 若把扁平分回"两段"（先全 pass1 再全 pass2），前奏和延迟收益都会消失——必须保持单循环。

## 适用场景
任何"两趟 softmax（求 max + 求 exp/和）→ 落盘 → 被另一核消费"的 CV 环；判据是 P/中间量是否在那另一核的关键路径上。

## Step 4: 边界与回退
- L0B 侧的对应手法（把 gemm 的 load/mma 拆成多 k-step 以重叠）不一定值得做：若 QK 的 mma 只占自身 fill 的一小部分，且 AIC 顶管是 MTE2，收益可能中性。**不是所有"两级流水"都值得做，先看顶管占比。**

## Step 3: 验证
- 同设备同窗口 batch paired；观察 SC→P 的到达时间与 PV 启动时刻。
- 逐例对比 max_abs_diff / matched_ratio；纯发射重排应逐位一致。
- 覆盖 d128/d64、不同 ngrp、最大 L2 span 的 case。

## 关联
- 与 [X176](../../optimizations/evolution_strategies/discovered/disc_x176.md)（scalar 等待判定）共享"关键路径不一定是指标最高的 pipe"的观点。
- 与 [X129](../../optimizations/evolution_strategies/discovered/disc_x129.md)（合批减少启动次数）从不同角度降低交付延迟。
