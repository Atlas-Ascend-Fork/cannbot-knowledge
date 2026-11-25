---
type: Optimization
title: "F22: 用「缩 baseK 换大 baseN」减少 A 重读，会让 burst 长度塌陷并净亏"
description: "用「缩 baseK 换大 baseN」减少 A 重读，会让 burst 长度塌陷并净亏；字节模型必须同时约束 burst 长度与扇区对齐。"
tags:
  - task.debugging
  - topic.programming_model.execution_unit.cube
  - topic.data_movement.data_copy
  - topic.memory
  - topic.tiling
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_strategy.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/transfer_larger_data_blocks.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f22_basen_upshift_collapses_burst_910b2c.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 baseN-upshift-collapses-burst-910b2c）。
>
> 原始元数据：
>
> ```yaml
> confidence: single_op
> phenomenon: perf_regression
> severity: high
> occurrences: 4
> failed_combination: [P105, P107, P117]
> op_families: [matmul, cv-mix]
> operator_type: matmul
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/f22_basen_upshift_collapses_burst_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f22_basen_upshift_collapses_burst_910b2c.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F: 用「缩 baseK 换大 baseN」减少 A 重读，会让 burst 长度塌陷并净亏

## 现象
针对权重流 GEMM 的 A 面板重复读取（realize 出 `baseM=48, baseN=32, baseK=168`，
`A` 按 n 组重读 12 次 = 14.8 MB/核 > 权重本身 12.6 MB），按**字节模型**把 tiling 改成
结果**全面回退**：

## 根因
`baseN` 与 `baseK` 在 L1/L0 预算是**互斥**的：baseN 涨到 256 后，为守住 L1 窗口必须把 baseK
压到 32，而 baseK 决定权重行的 **burst 长度**（baseK·4 = 128 B，改前 672 B）。
过短的突发让 MTE2 有效吞吐塌陷，把字节收益完全吃掉并倒亏。
说明 burst 存在**下界**（≈672 B 可用），但没有上界收益；越过下界立刻惩罚。

## Resolution
- **不要**为了减少 A 重读而降低 baseK。判据：改后 `baseK*4` 是否仍 ≥ 约 512~672 B；
- 若确实要减 A 重读，唯一安全的旋钮是**在 burst 不变的前提下抬 baseN**：
 本算子 realize 的 `(baseM=48, baseN=32, baseK=168)` 只用了 L0B 的 21.5 KB / 32 KB，
 请求更小的 baseN（使其不超过半 L0B）可降低 A 重读次数与每核字节，
 而 burst 仍是 672 B。**该旋钮现已实测**（ 补充）：把 baseN 抬到 L0B/L0C 上限
 L2 吸收、不花 HBM」：本算子单核 A 面板仅 0.2~8 MB，L2 有 192 MB。故该旋钮**安全但收益很小**，
 不要为它牺牲 burst 或核数。
- 与 F9（aic-byte-reduction-overlap-loss）同族：减少字节本身不等于提速，必须先确认被牺牲的
 另一维（重叠/突发/核数）不会同量级退化。
- **硬约束（多次复现，越界即崩）**：`baseN*baseK*4 ≤ L0B/2`（910B2C 上 L0B/2 = 32 KB）。
 realize 后的实际值、在同一处按序执行（见 F27）。

## 三次独立证伪（ 补充，occurrences 1→4）

同一条思路（「缩短 burst / 减少 A 扫描列数，换取更宽的 baseN」）在续跑会话里被**三种不同实现**
独立证伪，全部回滚：

**共同根因（比单一「burst 塌陷」更精确）**：按**扇区/请求字节**计价的模型忽略了
**MSHR 限制下的在飞字节** —— 缩短 burst 后同时在飞的上限下降（本例 336 KB→256 KB），
per-core MTE2 有效吞吐的损失大于省下的 A 重读。因此「请求数变少」不等于「时间变少」。
判据：任何以缩短 burst 为代价的候选，先看 `baseK*4` 是否仍 ≥ 512~672 B 且扇区对齐（X188），
否则直接丢弃，不要靠成本模型自我说服。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f22_basen_upshift_collapses_burst_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

