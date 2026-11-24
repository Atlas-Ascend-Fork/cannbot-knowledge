---
type: Optimization
title: tileLength 上板扫描标定（切分粒度校准）
description: 扫描参数化 tileLength，以实测平衡并行度和每-tile 固定开销，替换按 UB 倒推的默认值
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-tile-length-sweep-calibration.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：tileLength 上板扫描标定（切分粒度校准）

> 单一优化点：对参数化的 tileLength 做上板扫描，实测标定并行度与每 tile 固定开销的平衡点，替代"UB 越大越好"的推导默认值。

> 📌 **库内状态：定位修正——本卡是「标定工具」而非优化策略**。11 轮实测仅 2 轮有效，其中 **4/11 轮结论为 `already_applied`**（现行默认值已最优）。**不应计入优化策略成功率排名**；其用途是「验证默认 tile 是否已是 UB 倒推产物/是否已最优」。
>
> **前置判断（采纳第一步）**：先查现行默认 tile 是否已是 UB 预算倒推产物——若是，标定大概率得 `already_applied`，本轮应直接判 `no_applicable`/无优化空间，不必消耗实现轮次。

## 1. 原理
tile 数 = total/tile：粒度小→核并行度高但每核 tile 数多（循环+事件开销 ×N）；粒度大→每核搬运量大。平衡点在"tiles ≈ 1~3× 核数"附近，且对中小 shape（4 tiles@8192 只用 4/40 核）小 tile 显著提升核利用率。

- 改动量级：基础策略

## 2. 性能问题模式
- kernel 按 tile 循环（每 tile 固定开销：循环控制+队列事件+Pad 参数构造）；
- 默认 tile 从 UB 预算倒推（如"越大越好"），从未按实测标定，切分粒度失衡（MTE 低效搬运）。

## 3. 正确性红线
- UB 预算复核：in×BUFFER_NUM + out×BUFFER_NUM (+cast 中转 buffer) ≤ UB；
- tile 上限受 dtype 元素宽度约束（fp32 8192 元素双缓冲恰 128KB）。

## 4. 泛化条件
- **适用**：可推广至一切 tile 化多核 kernel；tileLength 已参数化（kernel 标量参数或可重编译常量）；需上板扫描。
- **不适用**：用推导代替扫描（每 tile 固定开销与 tile 数的平衡点只能实测）；tile < 2048 元素仍期望更快（实测 1024/2048 因循环开销显著变差：P7 6.66/4.57 vs 3.77us@4096）。

## 5. 实施步骤
1. tileLength 参数化（kernel 标量参数 + host env 覆盖，见 kernel-scalar-args-replace-tiling-struct）。
2. 扫 {8192, 4096, 2048, 1024} × 关键 shape，取 kernel 设备时间（非端到端，避免 host 噪声）。
3. 交叉复测两轮，定全 shape 不劣的最优档，固化为默认值，删 env 覆盖。

## 6. LLM 前置问题
- tileLength 是否已参数化（kernel 标量参数或可重编译常量）？
- 是否具备上板扫描条件（两轮交叉复测取 kernel 设备时间）？
- UB 预算是否复核（in/out×BUFFER_NUM + cast 中转 ≤ UB，dtype 宽度约束 tile 上限）？

## 7. 验收标准
- build + 精度全过；实测战绩（910B3）：定优 4096：P1 1.59→1.47、P7 3.84→3.76、P8 1.18→1.13；1024 档 P7 劣化至 6.66us（-74%）。

## 检索卡（短卡）

动作：扫描参数化 tileLength，以实测平衡并行度和每-tile 固定开销，替换按 UB 倒推的默认值
适用：适合 tileLength 已参数化且能够上板扫描的 tile 化多核 kernel
限制：输入、输出及 cast 中转缓冲区的总预算必须不超过 UB；本卡是标定工具而非优化策略，现行默认 tile 已是 UB 倒推产物时应判无优化空间
范围：tileLength 参数化的 tile 化多核 kernel
检索词：tileLength、上板扫描、UB 预算、核并行度、固定开销、关键 shape
机会：tile 仅由 UB 预算倒推且未经实测标定，切分粒度失衡
代价：小粒度增加循环与事件开销；大粒度增加每核搬运量
