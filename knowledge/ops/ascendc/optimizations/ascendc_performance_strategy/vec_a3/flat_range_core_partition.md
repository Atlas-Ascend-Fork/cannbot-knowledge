---
type: Optimization
title: 少段大块的扁平区间多核切分（flat-range-core-partition）
description: 将按段分核改为每核认领输出扁平连续区间，并扫描最大同源 run。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-flat-range-core-partition.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：少段大块的扁平区间多核切分（flat-range-core-partition）

> 单一优化点：按段粒度切核时若某 shape 段数 < 核数，绝大多数核空转、单核拷全量；改为每核认领输出扁平连续区间并做最大同源 run 扫描，恢复多核并行。

- **策略级别**：基础策略

## 1. 原理

"选择拷贝"类算子按**段粒度**把工作切给核时，若某 shape 的段数 < 核数（如 outer==1 → 3 段 / 50 核），**绝大多数核空转、单核拷全量**。本案例实测：单核拷 6-8MB 只有 ~160GB/s，而多核可达 500GB/s；r5 实验（几何坍缩成单段）使 P4 从 31.8us 恶化到 99.9us，直接实锤该缺陷。

段开销乘子模型只覆盖"段太多"，**必须同时检查"段太少"**（段数 < 核数 = 并行度崩塌）。

方案（mode3）：每核认领**输出扁平连续区间** [T×bid/C, T×(bid+1)/C)，区间内做最大同源 run 扫描，每 run 走三段队列流水按 tile 拷贝。

- 改动量级：基础策略

## 2. 性能问题模式

- "选择拷贝"类算子按段粒度切核，某 shape 的段数 < 核数（如 outer==1 → 3 段 / 50 核），绝大多数核空转、单核拷全量。
- 实测指纹：单核拷 6-8MB 只有 ~160GB/s，而多核可达 500GB/s；r5 实验（几何坍缩成单段）使 P4 从 31.8us 恶化到 99.9us。

## 3. 正确性红线

- run 边界的 (o,d,i) 分解用 int64 中间量（T 乘法溢出 int32）。
- full-slice 的 run 合并仅当 L==D（无行间 input 间隙）才合法。

## 4. 泛化条件

- **适用**：step==1 的"选择拷贝"类算子，段数 < 核数或整体覆盖（st==0 && sliceLen==dimSize）的 shape。
- **不适用**：step>1 的散位语义（由 strided-row-batch-assembly 覆盖）。

## 5. 实施步骤

1. host 路由：`step==1 && (numSegments < usedCores || (st==0 && sliceLen==dimSize))`。
2. kernel：每核认领**输出扁平连续区间** [T×bid/C, T×(bid+1)/C)，区间内做最大同源 run 扫描：
   - 切片内：src 偏移 `o*L*inner + (f-sliceB)`；**full-slice（L==D）时 src 跨行连续，run 延伸到 T**（否则停在本行切片尾）。
   - 切片外：input 恒等映射，run 延伸到本/下一切片起点（input 侧天然跨行连续）。
   - 每 run 走三段队列流水按 tile 拷贝。
3. 不硬编码任何 shape，几何参数全由 tiling 传入。

## 6. LLM 前置问题

- 该 shape 的段数是否 < 可用核数（或是否存在整体覆盖切片）？
- 是否 step==1（step>1 不适用本策略）？
- run 边界分解是否用 int64 中间量（防 T 乘法溢出 int32）？
- full-slice 的 run 合并是否仅在 L==D 时启用？

## 7. 验收标准

- build + 精度全过；实测（Ascend 910B3）：
  - P14 74→31us（0.68→**1.60×**）、P16 54→29us（**2.58×**）、P17 62→31us（0.72→**1.59×**，r7 补 full-slice 强制路由后）
  - geo 1.544→**1.621**

## 检索卡（短卡）

动作：将按段分核改为每核认领输出扁平连续区间，并扫描最大同源 run。
适用：适用于 step==1，且段数少于核数或切片整体覆盖维度的选择拷贝。
限制：run 边界的坐标分解必须使用 int64 中间量，避免 T 乘法溢出 int32。
范围：step==1 的选择拷贝类算子多核切分。
检索词：step==1、numSegments、usedCores、扁平连续区间、同源 run、int64
机会：shape 段数少于核数，导致多数核空转而单核承担全量拷贝。
