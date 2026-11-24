---
type: Optimization
title: 小 k topk 的手写向量化路径（替代高阶 TopK API）
description: 小 k 时以手写向量化路径替代高阶 TopK API；k=1 改走带索引的块归约 max。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/smallk-vectorized-topk.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：小 k topk 的手写向量化路径（替代高阶 TopK API）

单一优化点：当 topK 的 k 较小（典型 k ≤ 一个基本排序单元的宽度，如 k ≤ 8）时，用硬件排序原语 + 多路归并网络 + 位掩码提取手写实现 topk，替代高阶 TopK API；k=1 的极端情况直接用「带索引的块归约 max」一次产出 value+index。

## 1. 原理

高阶 TopK API 在小 k 下有固定开销与排序开销，且常走栈式 buffer、串行化严重。MoE 门控类算子的 k 多为 1/2/4，小 k 占绝大多数 case，高阶 API 是数量级瓶颈。

手写路径：
- **k=1**：直接用「按值排序、同时输出索引」的块归约 max 原语（ORDER_VALUE_INDEX 模式），一次得到最大值与它的位置，无需完整 topk。
- **1<k≤排序单元宽度**：对每行做硬件 32 元素排序（sort-32 原语），再用多路归并网络（典型 4 路归并）把多段排序结果合并，最后用位掩码（每 topK 元素 2 bit：值/索引交替）经 gather-mask 一次性提取前 k 个值与索引。全程裸向量原语，无栈式 buffer、无高阶 API 开销。
- 位掩码可由 k 直接构造（值掩码、索引掩码各一个字），k 小时一个掩码字足够。

## 2. 性能问题模式

- 输入末维 E、topK k，k 很小（1~8），E 任意。
- 现状：所有场景都走高阶 TopK API，承担其固定开销与排序开销；小 k case 延迟远高于目标性能（数量级差距）。
- 越是小 k，手写路径相对高阶 API 的优势越大。

## 3. 正确性红线

- **路由条件**：仅当末维对齐到排序单元宽度（如 E 是 8 的倍数）且 k ≤ 排序单元宽度时启用；否则回退到通用 topk 路径（见配套的大末维按块累积策略）。
- **k=1 路径**：块归约 max 必须用「值+索引」模式，索引指向末维位置；多个相等最大值时取首个（与基准一致）。
- **排序+归并+位掩码路径**：归并网络须稳定（相等值保持原序）；位掩码的值位/索引位布局须与 gather-mask 的 pattern 一致；提取后 k 个值按降序、索引对应。
- **padded 列**：[E, Ealign) 填充列在 softmax 后须掩成极小值（不参与 topk）。
- **bf16**：softmax/topk 在 float 上做，结果 cast 回；cast 须按对齐 stride。
- **输出**：topK 值同输入 dtype；专家索引/行位置索引 int32。
- **finished 哨兵**：带 finished 的行须短路（finished 行不参与正常 topk），可用向量化乘 + 广播 + 位掩码实现，不走高阶 API 的 finished 参数。

## 4. 泛化条件

- **适用**：k 小（≤ 排序单元宽度，典型 ≤ 8）且末维对齐到排序单元宽度；MoE 门控等小 k 场景。
- **不适用**：k 大（> 排序单元宽度）→ 用大末维按块累积策略；末维非排序单元对齐且无法廉价补齐。

## 5. 实施步骤

1. host tiling：按 (E 对齐?, k ≤ 排序宽度?) 路由；k=1 走「块归约 max 带索引」分支，1<k≤宽度走「排序+归并+位掩码」分支。
2. softmax 段：手写向量化（块归约 max → 减 → exp → 块归约 sum → 广播相除），与 topk 共用 on-chip buffer，避免重复搬运。
3. topk 段：k=1 → 块归约 max(value+index)；小 k → sort-32 → 多路归并 → 构造值/索引位掩码 → gather-mask 提取。
4. padded 列掩码、bf16 cast、行索引扇出、CopyOut。

## 6. LLM 前置问题

- k 多大？是否 ≤ 8？末维 E 是否对齐到 8？
- 当前 topk 是否走高阶 API？k=1 是否有专门分支？
- 是否有硬件排序原语 / 归并网络 / gather-mask 可用？

## 7. 验收标准

- build + 精度全过（topK 值与基准一致；索引顺序敏感输出按 case 集约定是否比对）。
- 小 k case 延迟显著下降，向目标性能靠拢。

## 检索卡（短卡）

动作：小 k 时以手写向量化路径替代高阶 TopK API；k=1 改走带索引的块归约 max。
适用：k 不超过排序单元宽度（典型≤8），且末维对齐；适合 MoE 门控小 k。
限制：仅在末维对齐且 k≤排序单元宽度时路由到该路径。
范围：topK 的末维 E 与小 k（1～8）路径。
检索词：TopK、硬件排序原语、多路归并网络、位掩码、块归约 max 带索引。
机会：小 k 仍统一走高阶 TopK API，承担固定开销与排序开销。
