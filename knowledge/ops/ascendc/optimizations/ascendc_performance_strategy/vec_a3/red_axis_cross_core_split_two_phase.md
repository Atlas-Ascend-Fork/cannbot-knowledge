---
type: Optimization
title: 归约轴跨核切分两阶段（partial 合并 final 单核）
description: 由仅按输出维分工改为跨核切分归约轴：第一阶段写fp32局部结果，第二阶段合并。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-red-axis-cross-core-split-two-phase.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：归约轴跨核切分两阶段（partial 合并 final 单核）

> 单一优化点：归约算子 work unit 仅按输出维划分导致 numUnits 极少、实占核数极低时，对归约轴做跨核切分，phase1 各核写 fp32 partial 行，phase2 单核合并写最终输出。

## 1. 原理

- 归约算子的 work unit 仅按输出维（outer×innerChunk）划分、归约轴从不切分：全归约/dim=首轴时 numUnits=1~4，实占核数 2.5~10%，并行损失 10~40x（扫描体积乘子超阈值）。
- 通过 tiling 增加归约轴切分参数（redSplit/segLen/totalSegs/partialStride），phase1 各核归约自己 (unit, red 段) 并写 fp32 partial 行；Path A 用 8 槽 32B 段槽——复制段值 8 份使 MTE3 32B 写不越界，合并对 sum/max/min 幂等。phase2（final）合并 partial + (1/p) Root + cast 写 y，final 用单核（blockDim=1）最稳。
- 改动量级：高阶策略（架构级重切分 + 两阶段 launch）。

## 2. 性能问题模式

- 归约算子的 work unit 仅按输出维（outer×innerChunk）划分、归约轴从不切分：全归约/dim=首轴时 numUnits=1~4，实占核数 2.5~10%，并行损失 10~40x（扫描体积乘子超阈值）。

## 3. 正确性红线

本案例踩坑，务必遵守：

- CMake `add_custom_command` 的 DEPENDS 必须含被 include 的头文件，否则改 .h 不触发重编（脏编译陷阱）。
- `DataCopyExtParams` 的 stride：src/dst 在 GM=字节，在 UB=32B 块单位；2D 搬 UB 时 blockLen 补 32B。
- MTE3 写 GM 按 32B 粒度，blockLen<32B 时 packed 布局会污染相邻数据（用 8 槽布局隔离）。
- TBuf 分配多大向量指令就只能写多大（4B buf 上 Adds(...,8) 会越界毁其它 buffer）。
- 直编译（bisheng -xasc）Vector kernel 未标记 kernel type 时，多核半精度实例有行为异常：小合并 kernel 单核最稳。

## 4. 泛化条件

- **适用**：归约轴从不切分、numUnits 极少（全归约/dim=首轴）导致实占核数极低的归约算子；扫描体积乘子超阈值的场景。
- **不适用**：存在未定位合并缺陷的组合场景——本案例 4 组 (布局,ordMode) 组合存在未定位合并缺陷，需降级守卫回单阶段路径保正确性。

## 5. 实施步骤

1. tiling 增加 redSplit/segLen/totalSegs/partialStride。
2. phase1：work=totalSegs，每核归约自己 (unit, red 段)，写 fp32 partial 行（Path A 用 8 槽 32B 段槽——复制段值 8 份使 MTE3 32B 写不越界，合并对 sum/max/min 幂等）。
3. phase2（final）：合并 partial + (1/p) Root + cast 写 y；final 用单核（blockDim=1）。
4. 对可能存在合并缺陷的 (布局,ordMode) 组合加降级守卫，回退单阶段路径。

## 6. LLM 前置问题

- 当前 work unit 划分是否导致 numUnits 极少、实占核数显著低于总核数？
- partial 写 GM 的 blockLen 是否满足 32B 粒度，是否需要 8 槽布局隔离？
- CMake DEPENDS 是否包含被 include 的头文件？final 合并 kernel 是否用单核？

## 7. 验收标准

- build + 精度全过；geo 0.3695→0.5094；P02 415→33us（11x）、P04 1444→51us（28x）；4 组 (布局,ordMode) 组合存在未定位合并缺陷，需降级守卫回单阶段路径保正确性。

## 检索卡（短卡）

动作：由仅按输出维分工改为跨核切分归约轴：第一阶段写fp32局部结果，第二阶段合并。
适用：归约轴未切分、numUnits极少而占核率低的归约算子；或扫描体积乘子超阈值的场景。
限制：CMake add_custom_command的DEPENDS必须包含被include的头文件。
范围：归约轴未切分且并行任务不足的归约算子。
检索词：归约轴跨核切分、redSplit、segLen、totalSegs、partialStride、fp32 partial、两阶段合并。
机会：work unit仅按outer×innerChunk划分，全归约或首轴归约任务数远少于可用核数。
代价：存在未定位合并缺陷的组合不适用。
