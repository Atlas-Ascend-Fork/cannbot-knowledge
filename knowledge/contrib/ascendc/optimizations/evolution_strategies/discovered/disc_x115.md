---
type: Optimization
title: "X115: tap 展平三级流水 + baseK 减半双份驻留"
description: "把 direct/im2col conv 的 (tap, kPanel) 两级循环展平为单迭代空间做三级阶梯流水，并减半 baseK 让 L0A/L0B 各驻两份 panel，使 MTE1 与 Mmad 重叠。"
tags:
  - task.optimization
  - topic.compute.neighborhood.convolution
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/typical_operator_cases/simd_operator_impl/matmul_matrix_operator/advanced_extreme_optimization.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/pipeline_scheduling/pipeline_scheduling.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x115.json
    role: evidence
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X115）。
>
> 原始元数据：
>
> ```yaml
> id: X115
> origin: discovered
> confidence: single_op
> op_families: [convolution, matmul, cv-mix]
> bottlenecks: [mte2_stall, partial_overlap, compute_bound]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x115.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x115.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X115: tap 展平三级流水 + baseK 减半双份驻留

## 核心思路
direct tap-decomposed conv（`acc[co,m] += Σ_tap W_tap @ x(m+off)`）的内层通常是
`for tap { for kPanel { LoadA; LoadB; SplitA; SplitB; Mmad } }` 的两级循环，每轮
LoadData3D(MTE1) 与 Mmad 严格串行，MTE1 吃不满。把 `(tap, kPanel)` **展平成一个迭代空间**
后做三级阶梯流水：

```
for it in [0, N):
 if it+2 < N: 下发 it+2 的 MTE2 (GM→L1)
 if it+1 < N: 下发 it+1 的 LoadData3D (L1→L0A/L0B, MTE1)
 做 it 的 Mmad
```

关键是让 **L0A/L0B 同时容纳两份 panel**：把 `baseK` 减半（本例 fp32 64→32）后，
两份 panel 的**合计占用**为 L0A = 2×baseM×baseK×4 = 2×128×32×4 = **32KB**、
L0B = 2×baseK×baseN×4 = 2×32×240×4 = **60KB**，分别不超过 910B2C 的
L0A/L0B 容量（各 **64KB**，见 `ASC_L0A_SIZE`/`ASC_L0B_SIZE`）。注意「2×」是两份 panel 合计，
不是每份 panel 各占 32KB/60KB；配置时须按「dst offset + transfer size ≤ 64KB」逐份核算并对齐。
配套：`a1q/b1q` 队列深度 2→4（两级预取），`a2q/b2q` 1→2。

## 适用场景
- 任何 direct/im2col conv 的 Cube 段（fp32/fp16），tap 数多（k≥3）时收益随 tap 数增大；

## 实现要点
- baseK 减半会增多 kPanel 数，但每 panel 的 Mmad 仍在 L0C 累加，总计算量不变；
- 队列深度受 L1 容量约束（A/B 各 2 份 + 预取 2 份）；先算清 L1 预算再改；
- L0A/L0B 预算必须按 `ASC_L0A_SIZE`/`ASC_L0B_SIZE`（910B2C 各 64KB）逐份核算两份 panel、
 对齐填充与其它常驻对象；若换了 dtype 或 baseM/baseN，需重新计算，不能沿用本卡的 32KB/60KB；
- 同轮配套收益：单核头阶段把它的小 DMA 合批（本例 fin2 的 fc/fcs 按 8 行 slab 一次载入，
 DMA 次数 ~1000+→~40），以及 crop 的常驻零区替代逐字节标量补零（注意 VEC 指令要求 32B 对齐，

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 问题现象
direct tap-decomposed conv 的两级循环 `for tap { for kPanel { LoadA; LoadB; Split; Mmad } }`
使 LoadData3D(MTE1) 与 Mmad 严格串行，MTE1 吃不满；L0A/L0B 只有单份 panel 无法预取。

## 精度验证

精度判据与逐 case 结果见证据包；正文只保留机制与适用边界。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x115.json`；引用时请结合上文适用条件与失效边界判断适用范围。

## 已证不可行
B(x) panel 的 ~11x tap 冗余不能在 L1 内按 tap 偏移复用（fp32 C0=8 vs kw 偏移 1 元素非 8 对齐）。