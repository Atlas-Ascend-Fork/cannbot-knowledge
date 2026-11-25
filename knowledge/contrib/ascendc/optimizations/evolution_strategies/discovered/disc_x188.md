---
type: Optimization
title: "X188: 权重流 GEMM 的 baseK「扇区对齐」判据"
description: "权重流 GEMM 的 achieved 带宽不只由 burst 长度决定，还要求 realize 后的 baseK 与 512B 扇区对齐；两者同时满足才能避免 burst 塌陷。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.data_movement.data_copy
  - topic.tiling
  - topic.alignment
  - topic.compute.quantization
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/gm_address_512b_alignment.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_mte2_preload.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x188.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X188）。
>
> 原始元数据：
>
> ```yaml
> id: X188
> origin: discovered
> confidence: single_op
> op_families: [matmul, cv-mix]
> bottlenecks: [mte2_stall, undersize_transfer, partial_overlap]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x188.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x188.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# X188: 权重流 GEMM 的 baseK「扇区对齐」判据

## 核心思路

权重流 GEMM 的 achieved 带宽不只由 **burst 长度**（baseK·4）决定，还要求 **realize 后**的
baseK 与 **512 B 扇区对齐**。本例算子 实测分水岭：

## 判据与实现

- 判据：dump realize 的 `baseK`，算 `baseK*4 % 512`；非 0 即嫌疑。
- 实现（纯 host，37 行）：候选搜索**拒绝** realize 后不对齐的候选；对不对齐的 incumbent 乘
 惩罚系数（本算子 1.78×）使其可被击败；若无任何对齐候选则原样返回 incumbent。
- 注意必须读 **API realize 后**的值 —— 请求值会被 `MatmulApiTiling` 钳位。

## 量化

## 适用条件与反例（ 补充，重要）

**适用条件**：可与「每块派发项 / 网格收窄」类改动（见 X189）**叠加**，两者作用于不同的桶，
不冲突。但可加性必须用**同一窗口的四臂 A/B** 证明，不能从跨会话的逐例比较推断。

**反例（曾经误判为冲突）**：上一轮曾诊断「扇区对齐」与「按派发成本收窄网格」两条改动

**各自拥有不同的桶，可加**，无抵消。

**误判根因**：原结论来自两次**分别测量**的变体逐例相减。本算子 35 个小 shape 上
**判据**：判「冲突/抵消」必须同窗口四臂；跨会话逐例比较只能用来生成假设。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x188.json`；引用时请结合上文适用条件与失效边界判断适用范围。

