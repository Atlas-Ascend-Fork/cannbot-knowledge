---
type: Optimization
title: 统一 32 元素行步长 + 批量 Cast 消除 per-row 指令
description: 将多行路径各UB buffer的行步长统一为32元素，把逐行Cast改为跨行批量Cast。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-unified-row-stride-batch-cast.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：统一 32 元素行步长 + 批量 Cast 消除 per-row 指令

> 单一优化点：把多行打包路径上所有 UB buffer 的行步长统一为 32 元素，使逐元素的连续向量流
> （输入 Cast、fp32→half→int8 Cast）可以一次全块调用，替代 per-row 循环内的多次指令 + barrier。
> 快的原因：行步长统一后连续流行正确，指令发射/同步次数按行数大幅下降（Abs/Cast 各 1 次）。

本策略适用于任何"多行打包 + 连续 Cast/类型转换流 + 行步长本不一致"的 kernel，与具体算子无关。

---

## 1. 原理

多行打包（baseRowLen>1）后，in/work/half/out 各 buffer 若行步长按各自 dtype 对齐（int32 8 元素、
fp32 8、half 16、int8 32），连续 Cast 流的行内偏移错位，只能退回 per-row 循环调用（每行一次
Cast+barrier）。把行步长统一为 **32 元素**（fp32 128B、half 64B、int8 32B、int32 128B 全部 32B
对齐），则每行偏移对每个 dtype 都是 32B 对齐，连续 Cast 逐元素正确 → Abs、Cast fp32→half、
Cast half→int8 各一次全块调用，指令数从 3×行数 降到 3。

## 2. 性能问题模式

1. 多行打包后 per-row 循环内有 Cast/Abs 等逐元素指令（每行调用一次 + barrier）。
2. 各 buffer 行步长对齐粒度不一致（如 in 8 元素、work 8、half 16、out 32），连续流必错位。
3. profiling：指令计数主导，小行宽 case 时间 >> 数据量下限。
4. 非对齐 H 时行步长 padding 差异加剧错位/崩溃（UB address not aligned）。

不适用：单行路径（baseRowLen=1，无跨行连续流）；无需 Cast 类型转换的算子。

## 3. 正确性红线

- **统一对齐值**：所有 buffer 行步长 = 同一元素对齐（32），最小步长≥32。
- **连续流行对应**：Cast(aF, aIn, curTileLen) 要求 aIn 与 aF 行偏移元素数相同（逐元素对应）。
- **int8 也 32B 对齐**：int8 行步长 = 32 元素 = 32B（非对齐值会让 Cast dst 未对齐崩溃）。
- **padding 清零**：H 非 32 倍数时行尾 padding 清零（清 0 条件用 `H % alignSizeIn != 0`，勿用固定 `%16`）。

## 4. 泛化条件

适用（任一）：
- 多行打包路径中 in→fp32→half→int8 类多级 Cast 的算子。
- 行步长因 dtype 差异而不同的多 buffer 算子。

不适用（任一）：
- 无跨行连续向量流的算子（per-row 独立 buffer 无错位风险，无需统一）。
- baseRowLen 恒=1 的算子。

## 5. 实施步骤

1. 确认多行路径各 buffer 行步长对齐粒度，选定统一元素对齐（32）。
2. tiling 的 UB 预算同步改为 32 元素对齐（与 kernel 一致）。
3. 把 Abs / Cast 循环改为全块单次调用；确保 src/dst 行偏移元素数一致。
4. 非对齐 H 的 padding 清零条件用 `H % alignSizeIn != 0`。
5. 全量编译，覆盖非 32 倍数 H（如 2049）与极小 H（如 16）验证精度。

## 6. LLM 前置问题

- 各 buffer 行步长当前是否一致？改为 32 元素对齐会多占多少 UB？
- 连续 Cast 的 src/dst 行偏移元素数是否一致？
- H 非 32 倍数时 padding 是否清零？

## 7. 验收标准

- 精度：全量通过（含 h=2049/4097 非对齐、h=16 极小）。
- 性能：小行宽多行 case 指令计数下降（本案例 case17 62→57us 等，整体 avg 1.04→1.16）。

## 检索卡（短卡）

动作：将多行路径各UB buffer的行步长统一为32元素，把逐行Cast改为跨行批量Cast。
适用：适用任一：多行打包路径含多级Cast；或多个buffer因dtype差异而行步长不同。
限制：所有 buffer 行步长统一为32元素且最小步长不小于32；tiling与kernel的UB预算对齐必须一致。
范围：多行打包路径的in、work、half、out等UB buffer。
检索词：多行打包、per-row、32元素行步长、批量Cast、in→fp32→half→int8、UB对齐
机会：per-row循环中每行执行Cast或Abs并伴随barrier，且各buffer对齐粒度不一致。
