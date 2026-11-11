---
type: Optimization
title: "X145: L0B 按 chunk 奇偶轮转的双 slot，重叠 K/V 填充与 mma"
description: "当 L0B 把 K 与 V 各占固定半区且单缓冲时，chunk c+1 的 MTE1 填充要等 chunk c 的 mma 读完同一 buffer，AIC 关键路径变成 Σ(装载+mma)。把 L0B 改成两个等大 slot 按 chunk 奇偶轮转（K 只被 C1 消费、V 只被 C2 消费，生命周期不相交），每 slot 一条 M_MTE1 信用，并删除因此冗余的 ring-tail 整迭代 drain，可让 fill 与 mma 重叠。"
tags:
  - task.optimization
  - topic.memory
  - topic.data_movement
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p153_l0b_parity_double_slot
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/51687dcbebee726b8c17c282ea6b02e19c6a23dd/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p153_l0b_parity_double_slot.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-skills/blob/9e6774cef47d8bc483ac83de3eb0620a740d042a/community/ops/ascendc-evolution-strategies/references/preconditions/P153.yaml
    role: constraint
created_at: "2026-10-28T11:30:00Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
---
# X145: L0B 按 chunk 奇偶轮转的双 slot，重叠 K/V 填充与 mma

> 已晋升为 [P153](../cards/p153_l0b_parity_double_slot.md)。本卡保留为发现记录。
>
> P 卡当前状态：`draft`（待实际算子正确性/性能验证证据）。

## 核心思路
MIX(CV) attention / matmul 类算子里，AIC 的 L0B 常被划成"K 固定半区 + V 固定半区"各占一半且各自单缓冲。此时同一 phase 内 chunk c+1 的 MTE1 填充必须等 chunk c 的 mma 读完同一 buffer（M_MTE1 串行握手），AIC 关键路径变成 `Σ(装载 + mma)` 而不是 `max(装载, mma)`。

验证点：先算 `Σ(装载+mma)` 与 `max(装载,mma)` 两个下界，若实测每迭代时间贴近前者，说明 L0B 单缓冲把装载与 mma 串行化了。

同一个 ring 迭代内 K 只被 C1 消费、V 只被 C2 消费，两者生命周期不相交。把 L0B 改成两个等大 slot、按 chunk 奇偶轮转（`slot = chunk & 1`）后，任一时间点的 slot 都空闲，填充只需等"上上次读过该 slot 的 mma"，于是 fill 与 mma 真正重叠。

## 适用场景
- AIC 侧 L0B 承载两个不同 phase 的 rhs（QK 的 K、PV 的 V），且每 phase 内部还要按列 chunk 切分。
- 单缓冲 L0B 导致每迭代墙钟接近 `Σ(装载+mma)` 而非 `max`。
- 反例：若某条 pipe 已完全饱和，或 L0B 必须同时容纳两种操作数（`cube_k` 很大时单 slot 就放不下），本策略不成立；需要先减小 tile 或改拆分方式。

## 实现要点
1. `l0b_slot = BLOCK_N_BASE * cube_k * sizeof(dtype)`；分配 `2 * l0b_slot`，K 与 V 的 chunk 都写进 `kv_l0[(chunk & 1) * l0b_slot]`。
2. 每 slot 一条 M_MTE1 信用：mma 读完该 slot 后 SetFlag，下一次填充该 slot 前 WaitFlag。信用在 task 循环前 preset 一次、循环后 drain 一次，保证每 task 内 Set/Wait 1:1 配平（计数恒在 {0,1}），kernel 退出无残留。
3. **必须删掉因此冗余的 ring-tail 整迭代 drain**（原"整迭代退休"的 M_MTE1 对），否则重叠被完全吃掉。只保留真正的 hazard：`acc_s_l0c → FIX_M`、`acc_s_l1 → MTE1_MTE2`。
4. 其余依赖（Q 常驻 L0A 的 reuse、cross-iteration 的 K/V 槽信用）要各自单列 id，不能与 slot 信用共用。
5. 数值零变化（只改填充与 mma 的顺序），可以作为纯调度优化直接落地；但仍需验证 flag 配平。

## 边界
- 若 `cube_k` 使单 slot 超过 L0B 容量的一半，双 slot 放不下；此时需要减小 chunk 或换 tile 形状。
- 若 mma 本身已是瓶颈，fill/mma 重叠的收益会被 mma 饱和吞掉。

## 验证方法
- 对比每迭代时间与 `Σ(fill+mma)` / `max(fill,mma)` 两个下界，确认瓶颈形态。
- 检查每个 task 的 Set/Wait 计数；长序列、尾块、不同 chunk 数。
- 同设备同窗口 A/B；数值逐位对比（纯调度改动应逐位一致）。

## 关联
- 与 [X149](disc_x149.md)（block_m 取满 L0C）可叠加：一个管 L0B 内 K/V 重叠，一个管 L0C 预算内的行数。
- 与 [X127](disc_x127.md)（RING/PRELAUNCH）共同涉及 ring-tail drain 的取舍。
