---
type: Runbook
title: "P153 Playbook: L0B 按 chunk 奇偶轮转的双 slot，重叠 K/V 填充与 mma 落地 SOP"
description: "完整发现记录见 ../../optimizations/evolution_strategies/discovered/disc_x145.md。"
tags:
  - task.optimization
  - topic.memory
  - topic.data_movement
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/discovered/disc_x145.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p153_l0b_parity_double_slot.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/1084df8aaa86b2e7a0ca4e723b4ea4b366cd3eeb/community/ops/ascendc-evolution-strategies/references/preconditions/P153.yaml
    role: constraint
created_at: "2026-11-03T15:14:30Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
aliases:
  - P153
---
# P153 Playbook: L0B 按 chunk 奇偶轮转的双 slot，重叠 K/V 填充与 mma 落地 SOP

> 证据状态：结构化来源为对应 X 发现记录（固定 commit）；实际算子的正确性/性能验证报告尚待补充。补齐前请把本卡视为待验证晋升，不用于强结论。

> 强制流程。完整发现记录见 [../../optimizations/evolution_strategies/discovered/disc_x145.md](../../optimizations/evolution_strategies/discovered/disc_x145.md)。

## Step 1: 取证

```bash
grep -nE "L0B|l0b|kv_l0" op_kernel/*.cpp op_kernel/*.h op_host/*.cpp op_host/*.h 2>/dev/null | head -50
```


## 背景与判定
MIX(CV) attention / matmul 类算子里，AIC 的 L0B 常被划成"K 固定半区 + V 固定半区"各占一半且各自单缓冲。此时同一 phase 内 chunk c+1 的 MTE1 填充必须等 chunk c 的 mma 读完同一 buffer（M_MTE1 串行握手），AIC 关键路径变成 `Σ(装载 + mma)` 而不是 `max(装载, mma)`。

验证点：先算 `Σ(装载+mma)` 与 `max(装载,mma)` 两个下界，若实测每迭代时间贴近前者，说明 L0B 单缓冲把装载与 mma 串行化了。

同一个 ring 迭代内 K 只被 C1 消费、V 只被 C2 消费，两者生命周期不相交。把 L0B 改成两个等大 slot、按 chunk 奇偶轮转（`slot = chunk & 1`）后，任一时间点的 slot 都空闲，填充只需等"上上次读过该 slot 的 mma"，于是 fill 与 mma 真正重叠。

## 适用场景
- AIC 侧 L0B 承载两个不同 phase 的 rhs（QK 的 K、PV 的 V），且每 phase 内部还要按列 chunk 切分。
- 单缓冲 L0B 导致每迭代墙钟接近 `Σ(装载+mma)` 而非 `max`。
- 反例：若某条 pipe 已完全饱和，或 L0B 必须同时容纳两种操作数（`cube_k` 很大时单 slot 就放不下），本策略不成立；需要先减小 tile 或改拆分方式。

## Step 2: 实施
1. `l0b_slot = BLOCK_N_BASE * cube_k * sizeof(dtype)`；分配 `2 * l0b_slot`，K 与 V 的 chunk 都写进 `kv_l0[(chunk & 1) * l0b_slot]`。
2. 每 slot 一条 M_MTE1 信用：mma 读完该 slot 后 SetFlag，下一次填充该 slot 前 WaitFlag。信用在 task 循环前 preset 一次、循环后 drain 一次，保证每 task 内 Set/Wait 1:1 配平（计数恒在 {0,1}），kernel 退出无残留。
3. **删除 ring-tail 整迭代 drain 前必须先做覆盖审计**：列出旧 drain 覆盖的全部读写与复用关系（共享物理地址、事件复用、跨迭代槽信用等），逐项说明由哪条新同步接管；只有全部覆盖后才能删除，仍有独立依赖的必须保留对应等待。审计通过后，才可删除因此冗余的整迭代 M_MTE1 对；真正的 hazard（如 `acc_s_l0c → FIX_M`、`acc_s_l1 → MTE1_MTE2`）仍需保留。
4. 其余依赖（Q 常驻 L0A 的 reuse、cross-iteration 的 K/V 槽信用）要各自单列 id，不能与 slot 信用共用。
5. 数值零变化（只改填充与 mma 的顺序），可以作为纯调度优化直接落地；但仍需验证 flag 配平。

## Step 4: 边界与回退
- 若 `cube_k` 使单 slot 超过 L0B 容量的一半，双 slot 放不下；此时需要减小 chunk 或换 tile 形状。
- 若 mma 本身已是瓶颈，fill/mma 重叠的收益会被 mma 饱和吞掉。

## Step 3: 验证
- 对比每迭代时间与 `Σ(fill+mma)` / `max(fill,mma)` 两个下界，确认瓶颈形态。
- 检查每个 task 的 Set/Wait 计数；长序列、尾块、不同 chunk 数。
- 检查同一物理地址的最后一次读取是否先于下一次写入，至少覆盖奇数 chunk、尾块和连续任务复用。
- 同设备同窗口 A/B；数值逐位对比（纯调度改动应逐位一致）。

## 关联
- 与 [X149](../../optimizations/evolution_strategies/discovered/disc_x149.md)（block_m 取满 L0C）可叠加：一个管 L0B 内 K/V 重叠，一个管 L0C 预算内的行数。
- 与 [X127](../../optimizations/evolution_strategies/discovered/disc_x127.md)（RING/PRELAUNCH）共同涉及 ring-tail drain 的取舍。
