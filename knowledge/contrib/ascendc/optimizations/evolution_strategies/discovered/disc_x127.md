---
type: Optimization
title: "X127: CV 环加深：RING 槽与 PRELAUNCH 的硬约束"
description: "CV 环里 PRELAUNCH 必须不大于 k_slots-1，超过会让 gather 等待一个尚未发出的信用而同核自锁；要增加在飞深度应增加 RING 槽，并把可证明冗余的消费者完成标记删除、将 FIX_M 排空推迟一迭代。每个被推迟的 Set 必须在 slot 收尾补 Wait，数量严格配平。"
tags:
  - task.optimization
  - topic.attention
  - topic.data_movement
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p149_ring_prelaunch_constraint
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/51687dcbebee726b8c17c282ea6b02e19c6a23dd/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p149_ring_prelaunch_constraint.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-skills/blob/9e6774cef47d8bc483ac83de3eb0620a740d042a/community/ops/ascendc-evolution-strategies/references/preconditions/P149.yaml
    role: constraint
created_at: "2026-10-27T16:00:00Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
---
# X127: CV 环加深：RING 槽与 PRELAUNCH 的硬约束

> 已晋升为 [P149](../cards/p149_ring_prelaunch_constraint.md)。本卡保留为发现记录。
>
> P 卡当前状态：`draft`（待实际算子正确性/性能验证证据）。

## 核心思路
在 MIX_AIC_1_2 的 C1/V1/C2/V2 环中，常见配置是 `RING=3 / PRELAUNCH=2`。加深在飞深度有两条路，但只有一条可行：

1. **只把 PRELAUNCH 2→3：物理不可行。** 迭代 t 的 C1 把 chunk t+1 gather 进槽 `(t+1) % k_slots`；该槽的上一读者是 chunk `t-k_slots+1` 的 C2，而 C2(tc) 在迭代 `tc+PRELAUNCH` 执行，因此必须满足
   `PRELAUNCH <= k_slots - 1`。
   若写成 3，gather 会等待一个"下一迭代才发"的信用，形成同核自锁（表现为挂死，不是精度问题）。
2. **RING 加深 + 迭代边界不全排空：可行。** 多出的环槽用来把"消费者完成"的排空跨迭代挂账：删除可证明冗余的标记（其 RAW 已被其他 flag 覆盖），把 `FIX_M`（ws_s fixpipe→M 管）的排空从上一迭代尾部推迟到下一 chunk 的 C1 头部；slot 末次在收尾处配对排空。

## 适用场景
- CV 环 + GM workspace（ws_s/ws_p/ws_o）的 mix kernel，环槽按 `num_cores * RING * slot_bytes` 分配。
- 加深 RING 后 host 侧 workspace 尺寸必须同步放大；L1/L2 有余量。
- 收益与"环是否真的挡住生产者"强相关。若生产者本来就不等环槽，加深不会有效。

## 实现要点
1. host 与 kernel 的 RING 镜像常量必须同步：ws_s/ws_p/ws_o 的 ring 维、`sp_core_base`/`o_core_base` 步长都要按新槽数重算。
2. 每个被推迟的 Set 必须在 slot 收尾补一次 Wait，**Set/Wait 数量严格相等**；否则跨 slot 残留 flag，最终死锁或静默错值。
3. 若某条流水段在新路径里不存在（例如 nomax 路径没有 fixpipe），对应 flag 对要整对删除，并用 tiling 门控避免失衡。
4. 短 slot（per_slot 很小）的形状可能因排空推迟而变慢；可用运行期 `per_slot` 阈值回退到"立即排空"。
5. 先用静态分析或轻量计数器证明 flag 配平，再做性能 A/B；不要用"跑通一次"代替配平证明。

## 验证方法
- 构造小 `k_slots` 与不同 `PRELAUNCH` 的组合，确认越界组合会挂死（用于验证约束理解）。
- 对每个 slot 收尾路径检查 Set/Wait 计数；跑长序列、尾块非整除、nomax/带 max 两条分支。
- 同设备、同窗口交错 A/B；环深收益通常较小，需排除测量漂移。

## 关联
- 与 [X128](disc_x128.md)（槽信用时序）和 [X157](disc_x157.md)（0x2 信用批量化）共同描述 CV 环的信用/槽管理。
