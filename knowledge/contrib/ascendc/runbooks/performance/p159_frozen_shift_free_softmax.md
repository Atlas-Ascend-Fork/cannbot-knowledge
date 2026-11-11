---
type: Runbook
title: "P159 Playbook: 有界 logits 下 softmax 去 frozen-shift 落地 SOP"
description: "完整发现记录见 ../../optimizations/evolution_strategies/discovered/disc_x174.md。"
tags:
  - task.optimization
  - topic.attention
  - topic.precision
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/discovered/disc_x174.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p159_frozen_shift_free_softmax.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/1084df8aaa86b2e7a0ca4e723b4ea4b366cd3eeb/community/ops/ascendc-evolution-strategies/references/preconditions/P159.yaml
    role: constraint
created_at: "2026-11-03T15:14:30Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
aliases:
  - P159
---
# P159 Playbook: 有界 logits 下 softmax 去 frozen-shift 落地 SOP

> 证据状态：结构化来源为对应 X 发现记录（固定 commit）；实际算子的正确性/性能验证报告尚待补充。补齐前请把本卡视为待验证晋升，不用于强结论。

> 强制流程。完整发现记录见 [../../optimizations/evolution_strategies/discovered/disc_x174.md](../../optimizations/evolution_strategies/discovered/disc_x174.md)。

## Step 1: 取证

```bash
grep -nE "Exp|Sub|reduce_max|softmax" op_kernel/*.cpp op_kernel/*.h op_host/*.cpp op_host/*.h 2>/dev/null | head -50
```


## 背景与判定
`softmax(z) = softmax(z - c)` 对任意行常量 c 成立。经典 online softmax 的 running-max 只用于防 exp 溢出。若目标算子的 QK 分数（乘 scale 后）有可证明的上界，且该上界在目标 dtype 的 exp 安全范围内，就可以**完全去掉 shift**：

- 直接 `exp(S * scale)`；
- `l` 与 PV 都只加不缩；
- 末尾一次 `acc_o / l`。

这样可以删除每个 tile 的 `reduce_max`、`Broadcast(m_i)` 与 `Sub`，减少 V 链的整 tile 运算遍数。

## 适用场景
QK 分数（乘 scale 后）有可证明上界，且在目标 dtype 的 exp 安全范围内；无界或分布未知时不适用。

## Step 2: 实施 — 证明义务
1. **上界**：`|s * scale|` 的最大值必须可静态界定，且 `exp(max)` 在 P 的 dtype 中不溢出。不能只凭"训练数据通常很小"就删 max。
2. **下界/下溢**：极小的 logits 经 exp 后可能下溢为 0；必须证明有效行的 `exp` 结果与分母 `l` 在目标 dtype 中仍可表示且不会出现 0/0。例如 logits `[-30, -31]` 转 fp16 后 exp 均为 0，分母为 0——只证明不溢出是不够的，还要做最坏输入误差验证。
3. **mask**：masked 元素仍依赖 `MASK_NEG`（例如 -30000）→ exp→0；不要为了去 shift 改 mask 值。
4. **logit_cap / tanh**：若存在 logit_cap 或 tanh 分支，上界证明必须覆盖该分支。
5. **dtype**：fp16 的 exp 安全范围比 fp32 窄；若 P 用 fp16，必须留足余量。

## Step 2: 实施
- 删除 `t==0` 的 `reduce_max_dyn<half>` + `Maxs(m_i, 0)`；
- 删除每个 tile 的 `Broadcast(m_i_2d_h) + Sub(s_half, s_half, m_i_2d_h)`；
- 保留 `Muls(scale)` / causal mask / `Exp` / l-defer / O 在 L0C / epilogue；
- 若保留 running-max 路径作为回退，host 侧应有门控开关，按 dtype/输入分布选择。
- V1 链从"多遍整 tile V 运算"降到"少一遍"，收益主要来自减少向量 op 数，而不是减少字节。

## Step 4: 边界与回退
- **只适用于有界 logits**；无上界证据时必须回退到 running-max（带 shift）。clamp 是逐元素截断，会改变 softmax 分布（如 `[12,13]` 截断到 11 后从 `[0.269,0.731]` 变成 `[0.5,0.5]`），不能作为等价回退，除非原算子契约本身要求截断并验证其语义。
- 若 P 的 dtype 是 fp16 且上界接近 exp 上限，去掉 shift 后即使不溢出也可能损失精度；应做最坏 max_abs 对比。
- 与 head-major/m_group 等布局/调度优化正交，可叠加，但叠加后要重新验证精度。

## Step 3: 验证
- 同设备 A/B vs 保留 frozen-shift 的版本；允许舍入差，但要看最坏 max_abs。
- 构造极端 logits 输入（最大/最小、mask 全行、logit_cap 开关）做压力测试。
- 全量精度 + 逐 case 对比；若任一 case Inf/NaN，立即回退。

## 关联
- 与 [X126](../../optimizations/evolution_strategies/discovered/disc_x126.md)（免 running-max + L0C 跨 chunk 累加）同属"先证明上界再省向量操作"，但 X126 省的是跨 chunk 重标定与 GM 往返，本卡省的是每个 tile 的 shift 运算。
- 与 [X149](../../optimizations/evolution_strategies/discovered/disc_x149.md)（block_m 取满 L0C）可叠加。
