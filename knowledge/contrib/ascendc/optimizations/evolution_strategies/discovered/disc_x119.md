---
type: Optimization
title: "X119: 行切片流的列宽/波数代价模型"
description: "行切片流的成本由列宽与波数决定；按 8KB burst 反推列宽、用波数代价模型选切分，并把累加器解耦，可避免窄列导致的 MTE2 事务膨胀。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
  - topic.tiling
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/tiling_strategy/tiling_strategy.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/data_move_guide/overview/data_move_concept.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x119.json
    role: evidence
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X119）。
>
> 原始元数据：
>
> ```yaml
> id: X119
> origin: discovered
> confidence: single_op
> op_families: [reduction, elementwise, attention, cv-mix]
> bottlenecks: [scalar_compute, undersize_transfer, tiling_imbalance, mte2_stall]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x119.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x119.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X119: 行切片流的列宽/波数代价模型

## 核心思路

纯 AIV 算子里最常见的形态是「沿通道轴取一段行、每行一段连续列」的行切片流。
成本由两个可解析推导的量决定，而不是靠试：

```
行段事务数 = b · c · ceil(n / W) # 与字节数无关，只与列宽 W 和行数有关
每笔事务字节 = W · sizeof(T)
总时间 ≈ max( 事务数 × 每笔固定延迟 , 字节数 / 有效带宽 ) × 波数
```

三件事可以解析地定：

1. **列宽由目标 burst 反推**：`W = min(n, 8192/sizeof(T))`（fp16/bf16→4096，fp32→2048），每笔落进 2~8KB。
2. **波数代价模型**：在候选列宽上最小化 `waves × (kLat + kVec·nb)`，而不是「凑固定波数」。
3. **fp32 累加器与块宽解耦**：归约可交换 ⇒ 块内偏移折进 `j % 512` 槽，宽 burst 不必配 `rows×width` 累加器，
 折叠仍是每任务一次。这是「宽 burst 不炸 UB」的前提。

## 适用场景与判据

纯 AIV 行切片流（通道注意力 / 门控 / per-channel 归约 / GEMV 链 / elementwise 融合）；
kernel 出现 `for c: DataCopyPad(每行 len)` 或 `b*ceil(n/W)` 形式的 grid，
且「有效带宽 ≪ 峰值」与「aiv_scalar_ratio 偏高」同时成立。

## 两条纪律

 ⇒ **scalar-issue bound 而非 bandwidth bound**；此时去「少流量」是白工（见 X118 的 wt 反例）。
- **并行度地板**：列宽放宽会让 task 数下降。`SplitColWidth` 只在必要时折半直到填满核数；
 只能靠加大窗口面积摊薄 flag 往返 —— X119 与 P1 在此形态下互斥。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x119.json`；引用时请结合上文适用条件与失效边界判断适用范围。

