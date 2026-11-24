---
type: Optimization
title: 片上容量自适应的归约 tile 放大
description: 将固定小归约tile改为按片上buffer实际容量自适应取齐并放大。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/ub-aware-reduce-tile.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：片上容量自适应的归约 tile 放大

单一优化点：把归约 tile 从固定小值改为按片上 buffer 实际容量自适应取齐（以占用 buffer 最多的 dtype/路径为最紧约束），放大 tile 以减少 tile 数与 DMA 往返。

## 1. 原理

带宽/归约密集型 kernel 若用**固定的小 tile**切分大 tensor，会产生大量 tile：每个 tile 带来一次 GM→片上 DMA 往返的启动开销、一次归约指令、以及一次（与 per-tile 回读策略叠加的）流水停顿。tile 数越多，固定开销与停顿叠加越严重，实测带宽利用率远低于峰值。

改为：把 tile 容量从「固定小值」提升到「按片上 buffer 实际容量自适应取齐」——在保证「输入 staging 队列（含流水深度）+ 计算所需全部片上 buffer」总和不超过片上容量的前提下，取尽量大的 tile。tile 越大，tile 数越少，DMA 往返与 per-tile 开销按比例下降，且更利于 DMA 与计算的流水重叠。

绑定约束：以「占用片上 buffer 最多的 dtype/路径」为最紧约束计算 tile 上限（如某 dtype 需要输入 staging 队列 + 多个等大同型计算 buffer），保证所有 dtype/路径都不会越界。

## 2. 性能问题模式

- 归约/带宽 kernel 用编译期固定的小 tile（与片上容量、tensor 规模都无关）。
- 大 tensor 被切成数千~上万 tile，墙钟里固定开销占比高、带宽利用率低。
- 改大 tile 后墙钟明显下降，说明 tile 数是主要放大因素。

## 3. 正确性红线

- tile 上限必须按「最紧 dtype/路径」的片上预算计算：输入 staging 队列（流水深度 × tile × 元素大小）+ 所有同时存活的计算 buffer（tile × 元素大小）+ 对齐/累加小 buffer，总和 ≤ 片上容量并留余量。
- 尾块（count < tile）必须由支持按元素个数的搬运/归约正确处理（带 pad 的搬运 + 按实际 count 的归约），不得假设整 tile。
- 改大 tile 后，归约指令的 shared-temp-buffer 容量须随 tile 同步放大（按归约对 count 的要求取齐）。
- 跨 tile 复用的 buffer 在下一 tile 覆写前，本 tile 的所有读须已完成（向量屏障）。

## 4. 泛化条件

适用：
- 带宽/归约密集型 kernel，当前固定 tile 远小于片上容量可承受的值。
- tensor 规模远大于 tile（多 tile 场景）。

不适用：
- tile 已接近片上容量上限（无放大空间）。
- 单 tile 即覆盖整核区间（tile 数本就为 1，放大无意义）。
- 放大 tile 会与其它约束（如同步、原子区）冲突且无法调和时。
- **反指纹（2026-09-22 新增）**：工作集 >L2 时放大 tile **反而降低有效带宽**（实测 16KB tile 已达 1.58TB/s，更大 tile 受 HBM/L2 行为限制不升反降）；此类算子不选。收益集中于少数重 case，小 case 会摊薄几何平均。

## 5. 实施步骤

1. 列出该 kernel 所有同时存活的片上 buffer 及其元素大小（输入 staging 队列按流水深度×tile、各计算 buffer 按 tile）。
2. 以「最紧 dtype/路径」求 tile 上限：tile ≤ (片上容量 − 对齐小 buffer) / (每元素占用字节数)，向下取整到对齐粒度。
3. 把 tile 从「固定小值」改为该自适应上限（或保守取其一部分留余量）。
4. 同步放大归约的 shared-temp-buffer 与各计算 buffer 的 InitBuffer 容量。
5. 确认尾块路径（count < tile）仍由按 count 的搬运/归约正确处理。
6. tiling 函数把该 tile 值随其它 tiling 参数下发到 kernel。

## 6. LLM 前置问题

- 当前 tile 是否为固定小值，与片上容量无关？
- 该 kernel 同时存活哪些片上 buffer？哪个 dtype/路径是片上预算的最紧约束？
- 片上容量是多少？按最紧约束能支撑多大 tile？
- 尾块（count < tile）与归约 shared-temp-buffer 是否会因 tile 放大而需要同步调整？

## 7. 验收标准

- 编译通过，安装包可用。
- 精度：与基线在共享评测用例集上逐用例一致（含非对齐尾块用例）。
- 性能：墙钟 mean 相对基线下降；大 tensor 用例下降幅度大于小 tensor 用例。
- tile 数相对基线显著减少；片上 buffer 总占用在容量预算内（不越界）。

## 检索卡（短卡）

动作：将固定小归约tile改为按片上buffer实际容量自适应取齐并放大。
适用：带宽或归约密集型kernel中，固定tile远小于片上容量，且tensor远大于tile。
限制：按最紧dtype/路径核算全部同时存活buffer、元素大小及staging流水深度；工作集>L2 时放大 tile 反降带宽，不适用
范围：带宽或归约密集型kernel的tile划分。
检索词：归约tile，片上buffer，容量自适应，输入staging队列，流水深度，多tile
机会：kernel使用与片上容量及tensor规模无关的编译期小tile，形成多tile结构。
代价：tile已接近片上容量上限时没有放大空间。
