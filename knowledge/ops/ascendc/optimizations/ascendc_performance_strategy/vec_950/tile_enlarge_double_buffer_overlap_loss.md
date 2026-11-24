---
type: Optimization
title: UB 填满式放大 tile 塌缩 per-core loopTimes 并丢失深度 2 双缓冲重叠
description: 按 shape 区间放大 tile 以减少 tile 数和逐 tile 标量工作，同时保留深度 2 双缓冲重叠。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/tile-enlarge-double-buffer-overlap-loss.md
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
      "tile 必须同时满足 UB 预算（逐槽 32B 对齐公式与 kernel InitBuffer 一致）与 DataCopyPad blockLen uint16 上限（max(xDtypeSize,maskDtypeSize)*te <= 65535）",
      "放大 tile 后每核 loopTimes 必须仍 >= 2（防御性守卫；防止未来更少核/更大 dtype 时深度 2 重叠丢失）"
    ],
    "excluded_conditions": [
      "放大后 per-core loopTimes < 2（每核只剩 1 个活动 tile，深度 2 双缓冲重叠必然丢失）",
      "小 shape（约 1-3M 元素、64 核下固定小 tile 只有约 4 tiles/core）且已确认 scalar/pipeline-management bound：填满式放大 tile 实测方向性回归（0.84-0.95x）"
    ],
    "required_conditions": [
      "kernel 使用 TQue BUFFER_NUM=2 深度双缓冲，Process 为串行 CopyIn->Compute->CopyOut 循环（无显式多级流水/屏障）",
      "kernel 由 tilingData->tileElements 完全参数化，host 改 tile 即可生效（host-tiling-only，kernel_hash 不变）",
      "瓶颈区间已用 profiling 确认（scalar/pipeline-management 或 MTE2 带宽受限）"
    ]
  },
  "classification": "negative_boundary",
  "evidence": [
    {
      "comparison_sha256": "d8ef717c9df02fb476a1b1cbca71d4ec2a8a91eb781e7b7a36097a80fba98a9d",
      "decision_sha256": "abde6761925cd11f691418e7edbfebe5cbeaa6735650373ae9701f710085abb6",
      "operator_class": "mask-predicate",
      "performance_sha256": "bd02bd04554c668c69a8ed6c3564b2ed220c85e5866f1d5d6264070d9d9b8908",
      "round": 1,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "cbeff31a1cbf34bf26a6d80aa55f686e82c5ccc3a9aaa79ba696ce9fcd7a962f",
      "verify_sha256": "674d154c80ba0ce6d1165845d2f5a51be4460fa42a114c97cb85256131cc6be4"
    },
    {
      "comparison_sha256": "2ca669c8a1833ac47acbfc5cfa7c86035deedbd54cc967d607feeb23923e5df4",
      "decision_sha256": "f483353a4caefc61fe8614926e2441ac8d4630067e0303a12d47431176f8ebc8",
      "operator_class": "reduction",
      "performance_sha256": "9fe1a4e9660c3b378d8848cf606c9d6e818f3705963b78f7fbe4a51dc2cb1b5f",
      "round": 3,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "291950a637f01f8003ddb49ae246e36f1adeabc60b89f26838ced4108e2d44f2",
      "verify_sha256": "29f67d9962909b8922e55293e81b537d481743f6b7fe46de662ad3c08af6d4c9"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-pipeline-bound",
      "mte2-bandwidth-bound"
    ],
    "guard": [
      "per-core-loopTimes>=2",
      "mtpe-bound-large-shape-only"
    ],
    "pattern": "tile-enlarge-double-buffer-overlap-loss",
    "structure": [
      "tque-double-buffer-depth2",
      "serialized-tile-loop",
      "host-tiling"
    ]
  },
  "generality": "common",
  "id": "NEG-TILE-DBUF-OVERLAP",
  "implementation_steps": [
    "先用 profiling 确认瓶颈区间（scalar/pipeline-management vs MTE2 带宽），对每个 shape 区间独立选择 tile。",
    "计算 dtype-aware 最大 tile 时同时检查 UB 预算与 DataCopyPad blockLen 上限（两条硬约束）。",
    "对放大候选计算 per-core loopTimes = CeilDiv(perCoreElements, tileElements)，仅当 >= 2 时采用；否则回退到保持深度 2 重叠的固定小 tile（如 4096）。",
    "按 totalElements 或 per-core loopTimes 分区：小 shape 保持原 tiling（loopTimes >= 4 的固定 tile），仅 MTE2-bound 大 shape 放大。",
    "在每核活动 tile 数不同的 shape 上分别验收，小 shape 不得出现方向性回归（median >= 0.95x）。"
  ],
  "intent": "削减 per-tile 标量/队列管理开销（scalar/pipeline-management bound），同时避免放大 tile 时丢失 TQue 深度 2 双缓冲重叠。",
  "mechanism": "host tiling 按 UB 预算（BUFFER_NUM*(AlignUp(te*x,32)+AlignUp(te*mask,32)+AlignUp(te*x,32)) <= ubSize，与 kernel InitBuffer 逐槽公式一致）和 DataCopyPad blockLen uint16 上限（max(xDtypeSize,maskDtypeSize)*te <= 65535）计算 dtype-aware 最大 tile，并覆盖所有 shape（无 per-core loopTimes / totalElements 守卫）。小 shape（64 核下固定小 tile 只有约 4 tiles/core）放大后 per-core loopTimes 塌缩到 1-2，深度 2 双缓冲重叠丢失，主目标回归；大 shape（每核 loopTimes 仍 >= 10）通过更少/更大的 MTE2 DataCopyPad 描述符提升有效 copy-in 带宽而获益——这是独立于目标机制的效应，不能挽救小 shape 回归。",
  "name": "UB 填满式放大 tile 塌缩 per-core loopTimes 并丢失深度 2 双缓冲重叠",
  "operator_scope": "Process 为串行 CopyIn->Compute->CopyOut tile 循环、TQue BUFFER_NUM=2 深度双缓冲、且 host tiling 由 tileElements 完全参数化的流式 kernel",
  "principle": "流式 kernel 的 UB tile 大小同时决定 per-tile 管理开销与每核活动 tile 数。放大 tile 到填满 UB 预算会减少总 tile 数（降低 per-tile 标量工作），但当 per-core loopTimes 塌缩到 1 时，串行 tile 循环中 BUFFER_NUM=2 的 ping-pong 双缓冲（相邻 tile 的 MTE2 搬入/MTE3 搬出与 V 计算重叠）被消除，内存延迟重叠的损失超过 per-tile 标量节省，净效果为回归。因此 tile 放大存在边界：仅在每核仍 >= 2 个活动 tile（loopTimes >= 2）且瓶颈为 MTE2 带宽时才有效。",
  "related_anti_patterns": [
    "tile-ub-budget-mismatch"
  ],
  "risks": [
    "填满 UB 预算后余量接近零：运行时 GetCoreMemSize(UB) 若返回更小容量或出现额外 UB 消费者，会触发设备错误 507015（UB 溢出）。",
    "把大 shape 的放大 tile 收益（更少/更大 MTE2 描述符）错误外推为所有 shape 通用，会在小 shape 上丢失深度 2 双缓冲重叠并回归。"
  ],
  "slug": "tile-enlarge-double-buffer-overlap-loss",
  "summary": "不要为削减 per-tile 标量/队列管理开销而把 UB 填满式放大 tile：当 per-core loopTimes 塌缩到 1-2 时，BUFFER_NUM=2 的深度 2 双缓冲内存延迟重叠被消除，小 shape 实测回归；放大 tile 只在 per-core loopTimes 仍 >= 2 且瓶颈为 MTE2 带宽的 shape 上有效。",
  "verification": {
    "correctness": [
      "放大 tile 后官方 correctness 通过（verify ok，kernel_hash 不变，host-tiling-only 改动）",
      "DataCopyPad blockLen 不超 uint16 上限，尾部/未对齐 shape（UpdateMask/tailRows 路径）结果正确"
    ],
    "performance": [
      "per-core loopTimes 塌缩到 1-2 的小 shape 不得出现方向性回归（实测反例：0.84-0.95x）",
      "放大 tile 仅在 per-core loopTimes >= 2 且 MTE2-bound 的 shape 上才可能获得收益（masked_scale 大 shape 实测稳定 1.11-1.27x）"
    ],
    "rollback_signals": [
      "放大后 per-core loopTimes < 2（守卫违例，深度 2 双缓冲重叠丢失）",
      "小 shape 中位数相对基线 < 0.95x（方向性回归）",
      "设备错误 507015（UB 溢出）或 DataCopyPad blockLen 超 uint16 字段上限"
    ]
  }
}
-->

# 性能优化策略：UB 填满式放大 tile 塌缩 per-core loopTimes 并丢失深度 2 双缓冲重叠

单一优化点：不要为削减 per-tile 标量/队列管理开销而把 UB 填满式放大 tile：当 per-core loopTimes 塌缩到 1-2 时，BUFFER_NUM=2 的深度 2 双缓冲内存延迟重叠被消除，小 shape 实测回归；放大 tile 只在 per-core loopTimes 仍 >= 2 且瓶颈为 MTE2 带宽的 shape 上有效。

## 1. 原理

流式 kernel 的 UB tile 大小同时决定 per-tile 管理开销与每核活动 tile 数。放大 tile 到填满 UB 预算会减少总 tile 数（降低 per-tile 标量工作），但当 per-core loopTimes 塌缩到 1 时，串行 tile 循环中 BUFFER_NUM=2 的 ping-pong 双缓冲（相邻 tile 的 MTE2 搬入/MTE3 搬出与 V 计算重叠）被消除，内存延迟重叠的损失超过 per-tile 标量节省，净效果为回归。因此 tile 放大存在边界：仅在每核仍 >= 2 个活动 tile（loopTimes >= 2）且瓶颈为 MTE2 带宽时才有效。

实现机制：host tiling 按 UB 预算（BUFFER_NUM*(AlignUp(te*x,32)+AlignUp(te*mask,32)+AlignUp(te*x,32)) <= ubSize，与 kernel InitBuffer 逐槽公式一致）和 DataCopyPad blockLen uint16 上限（max(xDtypeSize,maskDtypeSize)*te <= 65535）计算 dtype-aware 最大 tile，并覆盖所有 shape（无 per-core loopTimes / totalElements 守卫）。小 shape（64 核下固定小 tile 只有约 4 tiles/core）放大后 per-core loopTimes 塌缩到 1-2，深度 2 双缓冲重叠丢失，主目标回归；大 shape（每核 loopTimes 仍 >= 10）通过更少/更大的 MTE2 DataCopyPad 描述符提升有效 copy-in 带宽而获益——这是独立于目标机制的效应，不能挽救小 shape 回归。

## 2. 性能问题模式

- 优化目标：削减 per-tile 标量/队列管理开销（scalar/pipeline-management bound），同时避免放大 tile 时丢失 TQue 深度 2 双缓冲重叠。
- 适用数据流：Process 为串行 CopyIn->Compute->CopyOut tile 循环、TQue BUFFER_NUM=2 深度双缓冲、且 host tiling 由 tileElements 完全参数化的流式 kernel
- Feature signature：`{"bottleneck": ["scalar-pipeline-bound", "mte2-bandwidth-bound"], "guard": ["per-core-loopTimes>=2", "mtpe-bound-large-shape-only"], "pattern": "tile-enlarge-double-buffer-overlap-loss", "structure": ["tque-double-buffer-depth2", "serialized-tile-loop", "host-tiling"]}`

## 3. 正确性红线

- 填满 UB 预算后余量接近零：运行时 GetCoreMemSize(UB) 若返回更小容量或出现额外 UB 消费者，会触发设备错误 507015（UB 溢出）。
- 把大 shape 的放大 tile 收益（更少/更大 MTE2 描述符）错误外推为所有 shape 通用，会在小 shape 上丢失深度 2 双缓冲重叠并回归。

资源与硬件约束：

- tile 必须同时满足 UB 预算（逐槽 32B 对齐公式与 kernel InitBuffer 一致）与 DataCopyPad blockLen uint16 上限（max(xDtypeSize,maskDtypeSize)*te <= 65535）
- 放大 tile 后每核 loopTimes 必须仍 >= 2（防御性守卫；防止未来更少核/更大 dtype 时深度 2 重叠丢失）

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- kernel 使用 TQue BUFFER_NUM=2 深度双缓冲，Process 为串行 CopyIn->Compute->CopyOut 循环（无显式多级流水/屏障）
- kernel 由 tilingData->tileElements 完全参数化，host 改 tile 即可生效（host-tiling-only，kernel_hash 不变）
- 瓶颈区间已用 profiling 确认（scalar/pipeline-management 或 MTE2 带宽受限）

不适用：

- 放大后 per-core loopTimes < 2（每核只剩 1 个活动 tile，深度 2 双缓冲重叠必然丢失）
- 小 shape（约 1-3M 元素、64 核下固定小 tile 只有约 4 tiles/core）且已确认 scalar/pipeline-management bound：填满式放大 tile 实测方向性回归（0.84-0.95x）

## 5. 实施步骤

1. 先用 profiling 确认瓶颈区间（scalar/pipeline-management vs MTE2 带宽），对每个 shape 区间独立选择 tile。
2. 计算 dtype-aware 最大 tile 时同时检查 UB 预算与 DataCopyPad blockLen 上限（两条硬约束）。
3. 对放大候选计算 per-core loopTimes = CeilDiv(perCoreElements, tileElements)，仅当 >= 2 时采用；否则回退到保持深度 2 重叠的固定小 tile（如 4096）。
4. 按 totalElements 或 per-core loopTimes 分区：小 shape 保持原 tiling（loopTimes >= 4 的固定 tile），仅 MTE2-bound 大 shape 放大。
5. 在每核活动 tile 数不同的 shape 上分别验收，小 shape 不得出现方向性回归（median >= 0.95x）。

## 6. LLM 前置问题

- 目标实现是否满足：kernel 使用 TQue BUFFER_NUM=2 深度双缓冲，Process 为串行 CopyIn->Compute->CopyOut 循环（无显式多级流水/屏障）？
- 目标实现是否满足：kernel 由 tilingData->tileElements 完全参数化，host 改 tile 即可生效（host-tiling-only，kernel_hash 不变）？
- 目标实现是否满足：瓶颈区间已用 profiling 确认（scalar/pipeline-management 或 MTE2 带宽受限）？
- 是否命中排除条件：放大后 per-core loopTimes < 2（每核只剩 1 个活动 tile，深度 2 双缓冲重叠必然丢失）？

## 7. 验收标准

正确性：

- 放大 tile 后官方 correctness 通过（verify ok，kernel_hash 不变，host-tiling-only 改动）
- DataCopyPad blockLen 不超 uint16 上限，尾部/未对齐 shape（UpdateMask/tailRows 路径）结果正确

性能：

- per-core loopTimes 塌缩到 1-2 的小 shape 不得出现方向性回归（实测反例：0.84-0.95x）
- 放大 tile 仅在 per-core loopTimes >= 2 且 MTE2-bound 的 shape 上才可能获得收益（masked_scale 大 shape 实测稳定 1.11-1.27x）

回滚信号：

- 放大后 per-core loopTimes < 2（守卫违例，深度 2 双缓冲重叠丢失）
- 小 shape 中位数相对基线 < 0.95x（方向性回归）
- 设备错误 507015（UB 溢出）或 DataCopyPad blockLen 超 uint16 字段上限

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`common`
- Related anti-patterns：tile-ub-budget-mismatch

- masked_scale-20260823_153850-c68dfc（round=1, status=rejected）
- foreach_norm-20260823_153850-f56b93（round=3, status=rejected）

## 检索卡（短卡）

动作：按 shape 区间放大 tile 以减少 tile 数和逐 tile 标量工作，同时保留深度 2 双缓冲重叠。
适用：使用 TQue 双缓冲，且 Process 是无显式多级流水/屏障的串行搬入、计算、搬出循环。
限制：按实际UB容量和所有消费者核算并留余量；逐槽32B对齐，预算须与kernel InitBuffer一致。
范围：跨算子类的流式 kernel 串行 tile 循环。
检索词：UB tile、TQue BUFFER_NUM=2、CopyIn/Compute/CopyOut、per-core loopTimes。
机会：路径受逐 tile 标量/队列管理限制，且放大后每核 loopTimes 可能降至 1。
代价：tile 过大可能使双缓冲重叠失效。
