---
type: Optimization
title: "X174: 有界 logits 下 softmax 去 frozen-shift"
description: "softmax 对行常量平移不变；经典 online softmax 的 running-max 只用于防 exp 溢出。若能证明 QK 分数（乘 scale 后）在目标 dtype 的 exp 安全范围内且有上界，可完全去掉 shift，直接 exp(S*scale)，l 与 PV 只累加，末尾除 l。无界或分布未知时必须保留 max 或 clamp，否则 fp16 P 会溢出/NaN。"
tags:
  - task.optimization
  - topic.attention
  - topic.precision
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p159_frozen_shift_free_softmax
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/51687dcbebee726b8c17c282ea6b02e19c6a23dd/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p159_frozen_shift_free_softmax.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-skills/blob/9e6774cef47d8bc483ac83de3eb0620a740d042a/community/ops/ascendc-evolution-strategies/references/preconditions/P159.yaml
    role: constraint
created_at: "2026-11-02T16:31:31Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
---
# X174: 有界 logits 下 softmax 去 frozen-shift

> 已晋升为 [P159](../cards/p159_frozen_shift_free_softmax.md)。本卡保留为发现记录。
>
> P 卡当前状态：`draft`（待实际算子正确性/性能验证证据）。

## 核心思路
`softmax(z) = softmax(z - c)` 对任意行常量 c 成立。经典 online softmax 的 running-max 只用于防 exp 溢出。若目标算子的 QK 分数（乘 scale 后）有可证明的上界，且该上界在目标 dtype 的 exp 安全范围内，就可以**完全去掉 shift**：

- 直接 `exp(S * scale)`；
- `l` 与 PV 都只加不缩；
- 末尾一次 `acc_o / l`。

这样可以删除每个 tile 的 `reduce_max`、`Broadcast(m_i)` 与 `Sub`，减少 V 链的整 tile 运算遍数。

## 适用场景
QK 分数（乘 scale 后）有可证明上界，且在目标 dtype 的 exp 安全范围内；无界或分布未知时不适用。

## 证明义务（必须先做）
1. **上界**：`|s * scale|` 的最大值必须可静态界定，且 `exp(max)` 在 P 的 dtype 中不溢出。不能只凭"训练数据通常很小"就删 max。
2. **下界/下溢**：极小的 logits 经 exp 后可能下溢为 0；只要分母 `l` 仍能正确表示、且不会出现 0/0，通常可接受，但要逐 case 验证。
3. **mask**：masked 元素仍依赖 `MASK_NEG`（例如 -30000）→ exp→0；不要为了去 shift 改 mask 值。
4. **logit_cap / tanh**：若存在 logit_cap 或 tanh 分支，上界证明必须覆盖该分支。
5. **dtype**：fp16 的 exp 安全范围比 fp32 窄；若 P 用 fp16，必须留足余量。

## 实现要点
- 删除 `t==0` 的 `reduce_max_dyn<half>` + `Maxs(m_i, 0)`；
- 删除每个 tile 的 `Broadcast(m_i_2d_h) + Sub(s_half, s_half, m_i_2d_h)`；
- 保留 `Muls(scale)` / causal mask / `Exp` / l-defer / O 在 L0C / epilogue；
- 若保留 running-max 路径作为回退，host 侧应有门控开关，按 dtype/输入分布选择。
- V1 链从"多遍整 tile V 运算"降到"少一遍"，收益主要来自减少向量 op 数，而不是减少字节。

## 边界与失效条件
- **只适用于有界 logits**；无上界证据时必须保留 max 或加 clamp，否则 fp16 P 溢出/NaN。
- 若 P 的 dtype 是 fp16 且上界接近 exp 上限，去掉 shift 后即使不溢出也可能损失精度；应做最坏 max_abs 对比。
- 与 head-major/m_group 等布局/调度优化正交，可叠加，但叠加后要重新验证精度。

## 验证方法
- 同设备 A/B vs 保留 frozen-shift 的版本；允许舍入差，但要看最坏 max_abs。
- 构造极端 logits 输入（最大/最小、mask 全行、logit_cap 开关）做压力测试。
- 全量精度 + 逐 case 对比；若任一 case Inf/NaN，立即回退。

## 关联
- 与 [X126](disc_x126.md)（免 running-max + L0C 跨 chunk 累加）同属"先证明上界再省向量操作"，但 X126 省的是跨 chunk 重标定与 GM 往返，本卡省的是每个 tile 的 shift 运算。
- 与 [X149](disc_x149.md)（block_m 取满 L0C）可叠加。
