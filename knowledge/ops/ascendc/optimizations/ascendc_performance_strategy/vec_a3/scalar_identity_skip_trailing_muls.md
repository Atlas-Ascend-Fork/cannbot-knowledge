---
type: Optimization
title: 标量恒等式短路尾乘（scale==1.0 跳过 Muls）
description: Init记录scale是否为1.0；Compute仅在非1.0时执行尾部Muls。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-scalar-identity-skip-trailing-muls.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：标量恒等式短路尾乘（scale==1.0 跳过 Muls）

> 单一优化点：逐元素算子形如 `y = x ⊙ mask * s`（s 为运行期标量）时，把尾乘 `Muls(dst, dst, s, n)` 用 Init 期算好的 `skip = (s == 1.0f)` 条件包裹：恒等式成立时整条 VEC 指令消失。

## 1. 原理
`x * 1.0` 是 IEEE-754 精确恒等（含 -0.0/inf/NaN 传播不变）。每 tile 少发射 1 条向量
Muls 指令；对 VEC 指令数敏感的中小规模 case（~1M 元素，1-2us 量级）收益 2-12%。
判断在 Init 一次性完成（hoist），不进 tile 循环。

## 2. 性能问题模式
- 触发：逐元素 mul 类 kernel，尾乘标量来自 kernel 参数（编译期不可知），且评测/业务
  中该标量高频取 1.0（本例 20 case 中 12 个）。
- profiling 特征：VEC pipe 指令数偏多、单 tile 时延与指令条数线性可证。
- 不适用：标量恒为非 1 常量（编译器已折叠）、Muls 与其他指令已融合的场景。

## 3. 正确性红线
- 判断必须用 `s == 1.0f`（NaN != 1.0 自动走原路径，无需显式 isnan；kernel 上下文
  无 isnan/NAN 宏）。
- 不能推广到 `s == 2.0` 之类"可用移位替代"的伪恒等——只有乘 1.0（和加 0.0，注意
  -0.0 语义）是逐位无损的。

## 4. 泛化条件
- **适用**：任何"broadcast 标量 × 逐元素"尾乘/尾加，标量运行期已知。
- **不适用**：标量参与的是非恒等变换（round/shift 语义）。

## 5. 实施步骤
1. Init：`skipMuls_ = (scale == 1.0f);`
2. Compute：`if (!skipMuls_) Muls(...);`
3. 回归：非 1.0 case（0.5/2/inf/nan）必须持平——它们不走新分支。

## 6. LLM 前置问题
- 标量在真实负载中取 1.0 的频率多高？
- 判断式是否会被编译器外提？
- 尾乘标量是否可能为 NaN/inf，`s == 1.0f` 判断是否覆盖所有非恒等取值？

## 7. 验收标准
- build 通过，全量精度回归通过；非 1.0 case（0.5/2/inf/nan）逐位持平（不走新分支）。
- 卡内实测达标：s==1.0 的中小规模 case（~1M 元素）改善 2-12%。
- 判断在 Init 一次性完成（hoist），未进入 tile 循环。

## 检索卡（短卡）

动作：Init记录scale是否为1.0；Compute仅在非1.0时执行尾部Muls。
适用：逐元素mul内核的尾乘标量来自运行期参数，且当前值为1.0。
限制：必须用s==1.0f判断；NaN及其他非1.0值走原路径；非恒等round/shift语义不适用。
范围：逐元素mul内核的运行期标量尾乘。
检索词：标量恒等式、scale==1.0f、skipMuls、Muls、IEEE-754、hoist。
机会：逐元素结果末尾仍乘运行期标量s，而目标调用中s为1.0。
