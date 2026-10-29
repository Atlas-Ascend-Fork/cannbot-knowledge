---
type: Optimization
title: Cube 指令理论性能折算口径与峰值可达性判定
description: 固定单次 Mmad shape 的利用率公式含分形对齐膨胀与头开销 Δt；按 m/n 是否满 16、k 是否满 k0 算理论上界，供切分与搬运方案实测前参考，不代表整个实现的性能上界或收益排序。
tags:
- task.optimization
- topic.performance.analysis
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/cube_instruction_theoretical_perf_summary.md
  role: primary
created_at: '2026-10-28T07:35:00Z'
updated_at: '2026-10-28T07:35:00Z'
platforms:
- '950'
- a3
- a2
---

# Cube 指令理论性能折算口径与峰值可达性判定

Cube 的“理论算力”不是单一峰值数字；其中 Mmad 公式按固定单次计算的 shape 折算 cycle。本卡说明该公式的损失项、公式外成本，以及如何将其用于优化候选分析。文中数值均为**理论值，非实测**。

## 适用范围

- Ascend 950PR&950DT（`950`，NPU 架构版本 3510）、Atlas A3（`a3`）与 Atlas A2（`a2`，对应架构版本 2201）。两种架构的并行度常量取值不同，判断前必须先确认架构。
- 覆盖 Mmad 计算类、矩阵搬入类（L1→L0A/L0B/MX/BiasTable/Fixpipe）与矩阵搬出类（L0C→L1/UB）三类指令。

## 折算口径：只有两个损失项

Mmad 的文档公式可归纳为

```
利用率 = 理想cycle数 / (头开销 Δt + 对齐后cycle数)
       = [(m·n·k)/(cube_m·cube_n·cube_k)]
         / [Δt + (ceil_m·ceil_n·ceil_k)/(cube_m·cube_n·cube_k)]
```

其中 `ceil_m`、`ceil_n` 按 **16** 向上对齐，`ceil_k` 按 **k0**（L0 Buffer 上最小分型 K 方向大小）向上对齐；`cube_m`、`cube_n` 在所有 dtype 与两种架构下恒为 16；`cube_k` 随 dtype 变化；`Δt` 是头开销 cycle 数。

由此可直接得出：**公式内只有两项损失——分形对齐膨胀（乘性）与头开销 Δt（加性）。** 公式给出的是“对齐后的理论下限 cycle 数”，不是真实 cycle 数。凡是不能表达为这两项的损耗，都不在本公式能力范围内。

## 用公式做量化初判

对固定的单次 Mmad shape，把 `Δt` 置零可得该公式下的利用率上界，可作为对齐损失的初判。以 3510 的 float 为例（`cube_k` = 1、`k0` = 8），按公式推算：

| shape (m=n=k) | ceil 后体积 | 利用率上界（Δt=0，理论值） |
|---|---|---|
| m=n=8, k=8 | 16×16×8 | 0.25 |
| m=n=16, k=4 | 16×16×8 | 0.50 |
| m=n=16, k=8 | 16×16×8 | 1.00 |

读法：**在表中 m=n=8 的固定 shape 下，M/N 对齐带来两方向的乘性损失**——即使 K 已对齐，`Δt=0` 的理论利用率也只有 0.25；这不是改变切分、合并 shape 后的上界，更不是整个实现的性能上界。**K 不足 k0** 也是乘性损失：表中 k=4 对齐到 8，理论利用率上界腰斩。

## dtype 是量级变量，不是细节

`cube_k` 决定 K 方向每个 step 覆盖多少元素，因此同一 shape 换 dtype 会改变有效算力：half/bfloat16 为 16，int8 与 fp8 为 32，int4/fp4 为 64，开 HF32 的 float 为 8，而 float 在 2201 上为 4、在 3510 上为 1。同时 float 的 `k0` 恒为 8——**`cube_k` 小于 `k0` 意味着对齐粒度大于硬件并行度**，K 方向的膨胀代价被放大。

另一层量级差异来自产品规格：3510 上 float 算力为 half 算力的 1/16，开 HF32 后可提到 half 的 1/2，见[NPU 架构版本 3510](../../guides/programming_guide/advanced_programming/hardware_implementation/hardware_constraints/npu_arch_3510.md)。所以先确认 dtype 路线，再谈 Cube 调优；在 float 路径上按 half 的峰值预期做规划会高估一个数量级。

## unitFlag 不是调优旋钮

文档明确：在不同 shape 大小的情况下，unitFlag 的开关对性能**几乎无影响**。不要把 unitFlag 纳入性能实验矩阵，也不要把它当作对齐膨胀或搬运瓶颈的解释项。

## 公式之外的成本：理论峰值不可达的五类原因

1. **搬入/搬出带宽与延迟。** 搬运 cycle 数按 `data_size / bandwidth + ΔT` 计，而文档表格只给 `bandwidth`、**不含 `ΔT`**；小搬运时 `ΔT` 占比高，实际远慢于按带宽折算值。
2. **L0A 与 L0B 带宽不对称（2201）。** 两方向带宽不同，送 B 矩阵的通路更窄，因此“谁更慢”取决于搬运方向，不能只按总量估算。3510 上仅 `LoadData（2D矩阵搬运V2）` 的 L0A/L0B 表列带宽相同（256/256）；`LoadDataWithTranspose` 仍为 256/128，不可概括为所有 2D 搬运对称。
3. **量化路径多一条通路。** MX 类搬运按 `data_size/bandwidth + scale_data_size/bandwidth_mx + ΔT` 计，scale 数据走独立且更窄的通路，必须在预算里单列。
4. **兼容实现与布局塌缩。** 3510 上旧版 LoadData（2D）是走 V2 的兼容实现，文档指出会造成性能损失；LoadDataWithStride 不含跨版本兼容实现，表现更优。搬出的 NZ2DN 在 `srcNzC0Stride > 1` 时带宽与并行度同时塌缩，是容易漏掉的量级损失。
5. **L0/L1 容量与流水组织。** 容量约束、双缓冲与事件依赖均不在利用率公式内，需按 [L1/L0 双缓冲组织](../matmul/independent_l1_l0_double_buffering.md) 与 [静态切分与运行时 shape](../matmul/static_tiling_and_runtime_shapes.md) 单独核算。

## 判定：该不该继续优化 Cube 路径

1. **先算固定单次 Mmad shape 的对齐膨胀比。** 若 `m`、`n` 不是 16 的倍数或 `k` 不是 `k0` 的倍数，可将调整切分列为候选；切分会改变公式中的 shape，还须核算搬运、启动与流水成本，不能由乘性对齐项直接给方案排序。
2. **对齐不可改时看是否本质小 shape。** 若算法决定 `m` 或 `n` 小于 16 且无法合并，该单次 Mmad 的理论利用率受对齐限制；可评估合并 batch、沿 K 拆分累加或其他执行单元，但不能把该上界当作整个 Cube 路径的上界。
3. **对齐已满足仍不达预期？** 检查公式外成本：搬入/搬出的 `ΔT`、对应接口的 L0A/L0B 带宽、MX 双通路、兼容实现与 NZ2DN 布局；实际瓶颈须测量确认。
4. **以上都已排除仍不达预期？** 用 [Roofline 模型](../../concepts/roofline_model.md) 核对整个算子的访存/计算平衡点，并结合测量判断 Cube 是否为独立瓶颈。

## 失效边界

- 公式只覆盖固定 shape 的单次 Mmad 计算；改变切分或合并会改变代入的 shape，搬运、启动、同步、流水重叠与容量约束均不在内，不能据此预测端到端时延或跨方案收益。
- `Δt` 的具体取值文档未给，本卡只用 `Δt = 0` 的利用率上界做方向判断，不代表实际性能。
- 两种架构（2201 / 3510）的常量不可混用；跨架构比较必须分别代入。
- unitFlag 差异在文档口径下可忽略，不构成优化空间。
- 文档未提供实测标定，本卡不给“理论达成率”结论。

## 相邻卡分工与明细

| 卡片 | 分工 |
|---|---|
| [Cube 指令理论性能汇总（镜像卡）](../../apis/appendix/cube_instruction_theoretical_perf_summary.md) | 逐 dtype 的 `cube_k`/`k0` 常量与完整搬入搬出带宽表，本卡不复述 |
| [NPU 架构版本 3510](../../guides/programming_guide/advanced_programming/hardware_implementation/hardware_constraints/npu_arch_3510.md) | 架构级算力比例与分形布局变更 |
| [L1/L0 双缓冲组织](../matmul/independent_l1_l0_double_buffering.md) | 公式外的容量与流水重叠 |
| [静态切分与运行时 shape](../matmul/static_tiling_and_runtime_shapes.md) | 切分决策如何决定 m/n/k |
| [Roofline 模型](../../concepts/roofline_model.md) | 判断是否已转为访存受限 |
