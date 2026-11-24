---
type: Optimization
title: UB 计算链迁移到 RegTensor 驻留（中间结果不落 UB / Duplicate 广播替代标量读回 / DIST_UNPACK_B16 替代 fp32 staging）
description: 单一优化点：在 A5（DAV_3510）的 SIMD RegBase 载体下，把设计/翻译中"UB 中转"的计算链迁移到寄存器（RegTensor）驻留——中间结果不落 UB、Duplicate 寄存器广播替代标量读回、DIST_UNPACK_B16 替代 fp32 staging，避免"忠实翻译 TPipe/UB 词汇落到慢层"的载体错位。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/ub-compute-chain-regtensor-residency.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "寄存器驻留路径必须保持与 UB 版一致的数值语义（对齐、lane 数、舍入）；fp32 staging 改 DIST_UNPACK_B16 半精度拆包须单独核对精度与端序",
      "Duplicate 寄存器广播仅适用于可归约标量（每 256-slice 至多少量不同值 / 内维 stride-0 长 run）；不可归约的逐元素不同值不得强套",
      "跨 tile / 跨 core 需要交接的中间结果仍走 UB，寄存器无法跨边界驻留，不强行寄存器化"
    ],
    "required_conditions": [
      "目标芯片为 A5（DAV_3510，SIMD RegBase 载体）；A3/MemBase 不适用本卡",
      "计算链含中间结果落 UB 再读回（UB 中转），或标量读回、fp32 staging 等可迁移到寄存器的动作",
      "可归约的标量广播源存在于计算链中（可用 Duplicate 替代）"
    ],
    "excluded_conditions": [
      "纯搬移/拷贝类算子（无 UB 计算链，仅数据搬运）",
      "中间结果必须跨 tile/跨 core 经 UB 交接的归约/扫描（寄存器无法跨边界驻留，保留 UB 交接）",
      "fp32 精度门槛使 DIST_UNPACK_B16 半精度拆包不满足等价性要求的路径"
    ]
  },
  "classification": "meta_card",
  "created": "2026-09-21",
  "generality": "cross_op",
  "id": "VEC-CARRIER-UB-TO-REGTENSOR-RESIDENCY",
  "name": "UB 计算链迁移到 RegTensor 驻留（中间结果不落 UB / Duplicate 广播替代标量读回 / DIST_UNPACK_B16 替代 fp32 staging）",
  "operator_class": "vector",
  "origin": {
    "note": "载体适配元卡。依据 0916 gcd 单算子深挖与 0917 AB 批载体错位分析（策略选择流程再优化分析·补充点 1）聚合而成；三个分片机制（中间结果不落 UB、Duplicate 寄存器广播替代标量读回、DIST_UNPACK_B16 替代 fp32 staging）在 gcd 迭代中均已验证有效。属跨算子载体适配原则，无独立 run_id/sha256。",
    "evidence_status": "aggregated"
  }
}
-->

# 性能优化策略：UB 计算链迁移到 RegTensor 驻留（载体适配元卡）

单一优化点：在 A5（DAV_3510）的 SIMD RegBase 载体下，把设计/翻译中"UB 中转"的计算链迁移到寄存器（RegTensor）驻留——中间结果不落 UB、Duplicate 寄存器广播替代标量读回、DIST_UNPACK_B16 替代 fp32 staging，避免"忠实翻译 TPipe/UB 词汇落到慢层"的载体错位。

## 1. 原理

RegBase（RegTensor）载体的性能来自计算中间结果在寄存器内的驻留与向量宽度的利用；一旦中间结果每步落 UB 再读回、标量经 UB 读回、fp32 走 UB staging，就会把本该寄存器级完成的工作退化为 MTE2/VEC 往返，损失载体收益。

三个可独立采用的分片机制（均在 gcd 迭代中验证有效）：

1. **中间结果不落 UB**：计算链的中间张量尽量在 full-width 寄存器（RegTensor）内跨步/跨迭代驻留，避免每步 `SetValue`/`DataCopy` 回 UB 再读回的 MTE2/VEC 往返。
2. **Duplicate 寄存器广播替代标量读回**：对可归约标量（内维 stride-0 长 run、每 256-slice 至多少量不同值），用 ≤2 条基址对齐的 `Duplicate` 寄存器广播组装替代"标量读回再广播"的 UB 往返。
3. **DIST_UNPACK_B16 替代 fp32 staging**：对半精度（fp16/bf16）数据的 fp32 中转 staging，改用 `DIST_UNPACK_B16` 半精度拆包在寄存器内完成，省去 fp32 staging 的 UB 往返与带宽放大。

## 2. 性能问题模式

- 设计或策略卡翻译时把 TPipe/MemBase 时代的机制词汇（UB 中转、标量读回、fp32 staging）忠实地落到 A5 的 RegBase 载体上，导致中间结果频繁落 UB、标量经 UB 读回、fp32 走 staging，把寄存器级工作退化为 MTE2/VEC 往返。
- 典型现象：msprof 中 MTE2 往返占比偏高、VEC 管被标量读回/低效组装占据、目标路由相对同 shape 路由有 2~5x 结构性差距（载体错位，非算法错位）。

## 3. 正确性红线

- 寄存器驻留路径必须与 UB 版数值语义一致（对齐、lane 数、舍入模式）；fp32 staging 改 DIST_UNPACK_B16 半精度拆包须单独核对精度、端序与等价性门槛，不满足时回退 fp32 staging。
- Duplicate 广播仅适用于可归约标量；不可归约的逐元素不同值不得强套（会重新引入 bank 冲突或退化）。
- 跨 tile / 跨 core 需要交接的中间结果仍走 UB，寄存器无法跨边界驻留，不得强行寄存器化。
- 本卡只迁移 UB 计算链到寄存器，不改算子语义、不改 tiling/切分的正确性契约。

## 4. 泛化条件

- 策略作用域：cross_op（vector 类 A5 算子）。

适用：

- 目标芯片 A5（DAV_3510，SIMD RegBase 载体）；A3/MemBase 不适用。
- 计算链含中间结果落 UB 再读回、标量读回或 fp32 staging 等可迁移到寄存器的动作。
- 计算链中存在可归约标量广播源（可用 Duplicate 替代）。

不适用：

- 纯搬移/拷贝类算子（无 UB 计算链）。
- 中间结果必须跨 tile/跨 core 经 UB 交接的归约/扫描（保留 UB 交接）。
- fp32 精度门槛使 DIST_UNPACK_B16 半精度拆包不满足等价性要求的路径。

## 5. 实施步骤

1. 盘点开发方案中的 UB 计算链：列出哪些中间结果落 UB 再读回、哪些标量经 UB 读回、哪些 fp32 staging。
2. 对可归约标量广播源，用 ≤2 条基址对齐 `Duplicate` 寄存器广播替代标量读回。
3. 对半精度数据的 fp32 staging，评估 `DIST_UNPACK_B16` 半精度拆包路径，核对精度/端序是否满足等价性门槛。
4. 中间结果在寄存器内跨步/跨迭代驻留，减少回 UB 次数。
5. 跨 tile/core 必须交接的中间结果保留 UB 交接，不强行寄存器化。
6. 逐 case 正确性（对齐、精度）+ 稳定性核验，确认控制路由不变。

## 6. LLM 前置问题

- 目标算子是否 A5（DAV_3510）SIMD RegBase 载体？（设计期可判定）
- 开发方案的计算链是否含"中间结果落 UB 再读回""标量读回""fp32 staging"？（设计期可判定）
- 计算链中是否存在可归约标量广播源？（设计期可判定）
- msprof 是否显示 MTE2 往返占比偏高 / VEC 管被标量读回占据？（实施期复核）

## 7. 验收标准

正确性：

- 与 UB 版在容差内（或逐位）一致；DIST_UNPACK_B16 路径单独核对精度门槛。

性能：

- 目标计算链的 MTE2 往返、标量读回指令占比下降；目标路由相对同 shape 路由的结构性差距收窄。

回滚信号：

- 非 envelope lane 出现新增逐位差异，或精度超出等价性门槛。
- 目标路由 bank 冲突未下降或 vec_time 未按机制预测下降。
