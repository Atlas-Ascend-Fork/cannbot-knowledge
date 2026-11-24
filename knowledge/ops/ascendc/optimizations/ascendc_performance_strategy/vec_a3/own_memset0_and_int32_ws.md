---
type: Optimization
title: 自有 memset0 kernel + 值域无损 int32-ws 原子
description: 用自有memset0替换host清零；int64数据在输入、单段和与中间累加均在int32双边值域时可用int32 workspace。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.implementation.atomic
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-own-memset0-and-int32-ws.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-19T01:58:43Z'
platforms:
- a3
---

# 性能优化策略：自有 memset0 kernel + 值域无损 int32-ws 原子

> 单一优化点：host 侧 `torch::zeros`/`zero_()`（下发 aclnnInplaceZero，慢且有合规风险）
> 替换为自有字节级 memset0 kernel；int64 无硬件原子时的逐行 GM RMW fallback 替换为
> 值域无损 Cast int32 → int32-ws 原子累加 → castout，实测 10.4x。

## 1. 原理

- 自有字节级 memset0 kernel：Duplicate 清一块 UB tile，多核分块 DataCopyPad 写 0x00
  （对所有数值 dtype 0x00 即零位模式）。
- int64 无硬件 SetAtomicAdd（A2 上 int64 向量 Add 也静默出错），fallback 常写成逐行 GM
  read-modify-write：y 流量 2 倍 + 每行 MTE3→MTE2 同步。只有当每个 int64 输入、每个单段和
  以及 int32 原子累加的中间值都落在 [INT32_MIN, INT32_MAX] 时，Cast int64→int32 →
  int32 workspace 原子累加 → castout i32→i64 才可等价替换；若无法证明 Cast 截断与原子加
  的模 2^32 语义，必须保留 int64 路径。仅写“单段和 < 2^31”会漏掉大负数（如 -2147483649）。

## 2. 性能问题模式

1. 算子需要预清零输出或 workspace，host 侧用 `torch::zeros` / `y.zero_()`——会下发
   aclnnInplaceZero（aclnn 算子），既慢又有被评测 judge 判为"调用内置实现"的合规风险。
2. int64 数据无硬件 SetAtomicAdd（A2 上 int64 向量 Add 也静默出错），fallback 常写成
   逐行 GM read-modify-write：y 流量 2 倍 + 每行 MTE3→MTE2 同步。

## 3. 正确性红线

- **int32-ws 的双边值域门控**：必须同时满足以下条件，缺一不可：
  1. 每个 int64 输入 `x_i ∈ [INT32_MIN, INT32_MAX]`；Cast int64→int32 必须是无损转换。
  2. 每个单段和 `S_seg ∈ [INT32_MIN, INT32_MAX]`；不能只写 `S_seg < 2^31`，否则
     `-2147483649` 这类大负数会被误选。
  3. int32 原子累加的每个中间值也在 `[INT32_MIN, INT32_MAX]`；若实现依赖 Cast 截断和
     原子加模 2^32 的等价性，必须单独证明并写入卡片，否则按中间值约束处理。
  4. castout i32→i64 后必须仍等于真实 int64 结果。
  值域不可控或上述任一条无法证明时，必须走标量 int64 正确路径。示例 `|x|≤1e5、N≤4096
  → |单段和|≤4.1e8 < 2^31` 只是满足条件的一个特例，不能替代通用门控。

## 4. 泛化条件

- **适用**：任何需要预清零输出/workspace 的算子（memset0 部分，无值域前提）；int64 数据
  且每个输入、单段和与原子累加中间值都可证落在 `[INT32_MIN, INT32_MAX]` 的场景
  （int32-ws 部分）；小输出（ns*te ≤ ~10000）可改 per-core 标量 int64 累加 + merge kernel。
- **不适用**：输入或单段和可能越出 `[INT32_MIN, INT32_MAX]`、或无法证明 Cast/原子加
  无损的 int64 输入（走标量 int64 正确路径）。

## 5. 实施步骤

1. 自有字节级 memset0 kernel：Duplicate 清一块 UB tile，多核分块 DataCopyPad 写 0x00；
   替换全部 torch::zeros/zero_() 调用。
2. int64 值域无损时（每个输入、单段和与原子累加中间值均在 `[INT32_MIN, INT32_MAX]`，
   且 Cast/原子加语义已验证）：Cast int64→int32 → int32 workspace 原子累加 →
   castout i32→i64。
3. 小输出（ns*te ≤ ~10000）改 per-core 标量 int64 累加 + merge kernel。

## 6. LLM 前置问题

- host 侧是否存在 `torch::zeros`/`zero_()` 清零调用（合规与性能风险）？
- int64 输入的每个值是否可证落在 `[INT32_MIN, INT32_MAX]`？单段和与原子累加中间值是否也可证落在该区间（值域、N 与累加顺序是否已知）？
- Cast int64→int32 是截断还是饱和？int32 原子加溢出是否为模 2^32？是否有证据？
- 输出规模 ns*te 是否 ≤ ~10000（可走 per-core 标量累加 + merge）？

## 7. 验收标准

- build + 精度全过；实测证据（910B3, UnsortedSegmentSum level2）：
- case5 (int64, 4096x8192)：ZerosLike 4896us + RMW 16698us → memset0 311us + scatter 538us
  + castout 1233us（10.4x，含在 r1 整轮 0.40x→0.84x 内）
- 精度 20/20 全过（int32-ws 与 RMW 两种口径均过 golden）
- **负数/边界用例**：单输入 `INT32_MIN-1`（如 -2147483649）必须回退 int64 并输出正确；
  `INT32_MIN` / `INT32_MAX` 输入与单段和走 int32 路径且精确；最终和在 int32 内但存在
  越界输入（如 `2147483648 + (-1)`）或中间累加越界（如 `2147483647 + 1 - 1`）时，按声明的
  Cast/原子加语义验证，未证明则回退。

## 检索卡（短卡）

动作：用自有memset0替换host清零；int64数据在输入、单段和与中间累加均可证落在 [INT32_MIN, INT32_MAX] 时可用int32 workspace。
适用：预清零输出/workspace适用memset0且无值域前提；int64输入与单段和均在int32双边值域时适用int32-ws。
限制：int32-ws无损前提须同时约束输入、单段和与中间累加的双边值域（[INT32_MIN, INT32_MAX]），仅“和<2^31”会漏掉大负数；memset0写入0x00零位模式。
范围：输出/workspace预清零；满足值域条件的int64→int32工作区路径。
检索词：memset0、Duplicate、UB tile、DataCopyPad、torch::zeros、zero_、INT32_MIN、双边值域、int32-ws。
机会：输出或workspace需预清零，host侧仍调用torch::zeros或zero_。
