---
type: Optimization
title: "X189: X125 的两个边界——「每块派发项」该取、「cube 网格 cap」该弃、「stepN」已触顶"
description: "X125 把 L2 常驻权重 GEMM 的成本写成「每波请求行数」；本卡补充该目标函数的两个边界（该取「每块派发项」、该弃「cube 网格 cap」），并说明 stepN 已触顶。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
  - topic.precision
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_l2_cache_split.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_strategy.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x189.json
    role: evidence
created_at: "2026-10-29T00:00:00Z"
updated_at: "2026-10-29T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X189）。
>
> 原始元数据：
>
> ```yaml
> id: X189
> origin: discovered
> confidence: single_op
> op_families: [matmul, cv-mix]
> bottlenecks: [tiling_imbalance, mte2_stall, ub_memory_pressure]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x189.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x189.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# X189: X125 的两个边界——「每块派发项」该取、「cube 网格 cap」该弃、「stepN」已触顶

## 核心思路

X125 把 L2 常驻权重 GEMM 的成本写成「每波请求行数」。本轮在该目标函数上补三件事，
并用**隔离测量**（每项单独开/关）而不是打包测量来定边界：

1. **加一个每块派发项**：调度一个 block 不是免费的。同 shape、只改网格的两点实测
 （`wpm_gelu` 48 块 5.94us vs 4 块 2.36us → 44 块 = 3.58us）解出 **81 ns/块 + 2.03us 地板**。
 把它写成 `cost = blocks*81ns + waves*rows*(REQ_FIXED + bK*4/BW)`，`blocks = min(tiles, aicCores)`，
 并同步把 AIV 段的 `BLK_DISPATCH_US` 0.065→0.081、`BLK_MIN` 4→2。
2. **不要把 cap 推广到 cube 网格**：把同一个 `cap = max(BLK_MIN, ceil(sqrt(work/dispatch)))`
 套到 c_emb/proj/fc2 上会**净亏**。
3. **stepN（L1 N 多 tile）有硬顶**：它是「不缩短 burst 而加宽 A 复用窗口」的唯一合法旋钮，

## 判据与约束

- 派发项只对**每块工作量已低于派发单价**的段有意义（本例：纯 AIV 段与 M 只有 7~44 行的
 L2 常驻小 GEMM）。工作量大到 `blocks` 由工作量决定的段不受影响。
- stepN 硬顶判据：`singleCoreN` 侧的 L1 窗口 `≈ stepN*stepKb*baseK*4`（含双缓冲）。
 本例主导大桶几何 `(bM=32,bN=32,bK=256,stepN=4)` 占 **327,680 / 393,216 B**，
 下一步 stepN 需 **589,824 B** ⇒ 在不缩短 burst、不增加 m-tile 的前提下**无合法点**。
- 仍受 X125 的硬约束：一核一个 base tile、`baseN ≥ 32`、`bM·bK`/`bN·bK` ≤ 半 L0A/L0B、

## 量化（本例算子, 910B2C, 同窗口 A/B）

- 派发项单独就拿到了小桶几乎全部收益（2.2522→2.3330），**且它不需要任何几何改动**。
 192→256KB）⇒ 相对父节点 n44 基本持平。
- 与几何侧合并后（X188 扇区对齐 + baseN 抬升 + 本卡的派发项 + stepN），收益可叠加；定量见证据索引。

## 按 bucket 可加（重要）

两项改动不是「互相抵消」，而是**各自拥有不同的桶**：四臂同窗口 A/B 中

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x189.json`；引用时请结合上文适用条件与失效边界判断适用范围。

