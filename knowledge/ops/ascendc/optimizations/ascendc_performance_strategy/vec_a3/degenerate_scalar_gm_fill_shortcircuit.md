---
type: Optimization
title: 退化标量输出短路为纯 GM Fill（NaN-scale FillNaN）
description: 标量为 NaN 时跳过输入读取与常规计算，改用大 UB 缓冲 Duplicate 后循环 DataCopy 填充输出。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-degenerate-scalar-gm-fill-shortcircuit.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：退化标量输出短路为纯 GM Fill（NaN-scale FillNaN）

> 单一优化点：当逐元素算子的输出对某标量参数退化为常量（如 `y = x*mask*NaN ≡ NaN`），整个 kernel 短路为"一个 UB 大缓冲 Duplicate 常量 + round-robin 广播 DataCopy"：不读任何输入，VEC 只离开关键路径一次，case 变成纯 MTE3 写吞吐。

## 1. 原理
IEEE 传播保证任何元素与 NaN 相乘结果为 NaN，与 x/mask 无关 → 2/3 内存流量（读 x、
读 mask）直接消失。单次 count-mode Duplicate 填 ~180KB UB（910B3 192KB UB 的 94%），
随后 back-to-back DataCopy 让 MTE3 带宽饱和。实测 case13（10M 元素 f32/f32 NaN）
78.5us → 14.2us（-80%，5.4x）。

## 2. 性能问题模式
- 触发：逐元素算子存在"标量使输出退化为常量"的数学事实（NaN 乘、×0 得 0 等，需
  注意 ×0 对 inf/NaN 输入不恒等于 0——只有 NaN 乘对全输入空间成立）。
- profiling 特征：该参数取退化值的 case 耗时与正常 case 同量级（读满输入带宽）。
- 不适用：输出不退化（任何参数值都要读输入）；退化值依赖输入元素值。

## 3. 正确性红线
- 只有 `* NaN` 型对全输入空间逐位成立；`* 0` 对 inf/NaN 输入输出 NaN 而非 0，
  不可同样短路（除非业务确认输入有限）。
- kernel 上下文无 NAN 宏：用 `0.0f/0.0f` 构造。
- fill 元素数取 `UB_budget / sizeof(T)` 向下取整（天然 32B 对齐）；全局唯一 tail
  保持 DataCopyPad。
- round-robin 覆盖：tile t 归 core t%numBlocks，并集恰为 [0,N) 无重叠。

## 4. 泛化条件
- **适用**：逐元素算子 + 标量退化常量；常数填充类任务。
- **不适用**：归约/拼接等输出依赖输入结构的算子。

## 5. 实施步骤
1. Init：`scaleIsNan_ = (scale != scale);` 为真则只 InitBuffer 单个大 out 队列并 return。
2. Process：短路到 FillNaN（Duplicate + 循环 DataCopy）。
3. 精度：退化 case 输出全 NaN 与 golden 逐位比对。

## 6. LLM 前置问题
- 退化是数学恒等还是业务近似？
- ×0 型短路是否被输入域排除？
- kernel 上下文是否可用 NAN 宏，还是必须用 `0.0f/0.0f` 构造？

## 7. 验收标准
- build 通过，全量精度回归通过（退化 case 输出全 NaN 与 golden 逐位一致，非退化 case 走原路径持平）。
- 卡内实测达标或预期：退化大 case（如 10M 元素 NaN）端到端耗时显著下降（本例 78.5us → 14.2us，-80%，5.4x），case 退化为纯 MTE3 写吞吐。
- round-robin 覆盖并集恰为 [0,N) 无重叠、无越界；fill 元素数满足 32B 对齐。

## 检索卡（短卡）

动作：标量为 NaN 时跳过输入读取与常规计算，改用大 UB 缓冲 Duplicate 后循环 DataCopy 填充输出。
适用：适用于标量使逐元素输出恒定的算子及常数填充任务。
限制：仅可短路全输入空间成立的恒等式；×0 不覆盖 inf/NaN，归约或拼接不适用。
范围：标量退化常量的逐元素输出路径。
检索词：scaleIsNan、FillNaN、Duplicate、DataCopy、常量退化。
机会：逐元素输出因某标量在全输入空间退化为常量。
代价：大缓冲示例占约 192KB UB 的 94%。
