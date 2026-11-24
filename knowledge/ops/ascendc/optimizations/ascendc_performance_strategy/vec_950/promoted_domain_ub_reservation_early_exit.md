---
type: Optimization
title: 提升域持久态早退：host tiling 为提升后中间态预留 UB 窗口
description: 在host tiling的目标dtype分支按原生宽度2倍预留UB，使kernel可跨chunk持久化提升域中间态。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/promoted-domain-ub-reservation-early-exit.md
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
      "预留只作用于目标 dtype 分支，其他 dtype 的 tiling/ubFactor 必须逐字节不变",
      "host 预留与 kernel TBuf 必须精确对账，否则 UB 溢出",
      "提升域真 abs（如 abs(-32768)=32768）必须在提升后、abs 之前执行以保位精确",
      "缩窄出口（wrap-cast）必须与原始路径一致，覆盖全 dtype 域（含极值）"
    ],
    "excluded_conditions": [
      "提升域中间态可压回原生宽度存储（无需持久化提升域状态）时不适用",
      "host tiling 无法单独调整（如编辑范围只允许 kernel）且无法复用现有窗口时，此机制需先解除编辑范围限制",
      "非 VEC-bound route 不预期从该机制获得时延收益"
    ],
    "required_conditions": [
      "热链为提升域计算：窄 dtype 提升到宽 dtype 域执行，且分块早退机制需要在 chunk 间持久化提升后的中间态",
      "host tiling 有独立的 UB 预算（simdWorkB/ubFactor），且当前未为提升域持久态预留窗口",
      "kernel 与 host 能精确对账预留字节与 TBuf 注册字节",
      "I/O cast 边界（提升 + 真 abs、wrap-cast 缩窄）可逐字保持原始语义"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-24",
  "evidence": [
    {
      "case": "T1(1,4,8,12,16,19)",
      "operator_class": "broadcast",
      "round": 2,
      "run_id": "<run-id>",
      "speedup": "T1 int16 2.73-5.72x; T2/T3 control 保持 round-1 中位数 (<0.05% 偏差); total 4.4726",
      "status": "accepted"
    },
    {
      "comparison_sha256": "c05f5a85cfa0946e6b06c396e0eb29f39529400e855935d0fb4171e9c7511841",
      "decision_sha256": "532588d3a547ad447b26d00995d2ed64a829f46a43a08156873dd37e7e305549",
      "operator_class": "broadcast",
      "performance_sha256": "17c3027eccdabc9f04a5d69f2394118599e28b2999d9c5b2e471bb940eaed371",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "67c219c8f3f0b7318fae7b7e28e4c2ee19479c846bb07425ef65aa90d0bb27b9",
      "verify_sha256": "f198f84aa6061334e1db7bb0032448d2b7c85dc49f4144033e1395850d48a02b"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "fixed-round-loop",
      "promoted-domain-ub-pressure"
    ],
    "dtypes": [
      "int16"
    ],
    "pattern": "promoted-domain-persistent-state-ub-reservation",
    "structure": [
      "dtype-promotion",
      "vec-iterative-loop",
      "host-ub-budget",
      "ub-persistent-state"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-PROMOTED-DOMAIN-UB-RESERVATION",
  "implementation_steps": [
    "确认热链在提升域执行且分块早退机制需要持久化提升后中间态，评估 2x 原生宽度 UB 缺口",
    "在 host tiling 中对目标 dtype 分支预留 2 * CeilAlign(VF_ELEMS * sizeof(提升域 dtype), 32) 字节，其他 dtype 分支不动",
    "kernel 注册匹配的提升域持久化 TBuf，chunk 循环复用原生域分块 VF 轮体",
    "保持 I/O cast 边界逐字一致（提升 + 真 abs、wrap-cast 缩窄），跑全 dtype 域 verify（含极值）",
    "验证其他 dtype route 无 tiling/性能回归，实测调参 K 与 done 检查频率"
  ],
  "intent": "解除'提升域中间态超出 host tiling UB 预算'对早退机制的排除，把分块早退收益扩展到 dtype 提升的窄整型 route。",
  "mechanism": "在 host tiling 的 simdWorkB 计算后，对目标窄 dtype 分支追加预留 2 * CeilAlign(VF_ELEMS * sizeof(提升域 dtype), 32) 字节（int16 提升 int32 时 +2048B，ubFactor 收缩 <1%），其他 dtype 分支的 tiling 完全不动；kernel 侧注册两个提升域持久化 TBuf（各 VF_ELEMS * 4B），chunk 循环直接复用原生域的分块 VF 轮体，I/O 边界（窄 dtype 加载 -> Cast 提升 + 真 abs -> 提升域 chunk -> wrap-cast 缩窄 -> 窄 dtype 存储）与原始路径逐字一致。",
  "name": "提升域持久态早退：host tiling 为提升后中间态预留 UB 窗口",
  "op": "gcd",
  "operator_class": "broadcast",
  "operator_scope": "把分块全 lane 早退机制扩展到 dtype 提升计算域（窄整型提升到宽整型域执行逐元素迭代，如 int16 提升 int32 计算欧几里得）的流式 elementwise route；热链仍 VEC-bound，且新机制需要在 chunk 间持久化提升后的中间态",
  "principle": "当计算在提升域（窄 dtype 提升到宽 dtype）执行、且机制需要在 chunk 间持久化提升后的中间态时，UB 需求是原生宽度的 2x；host tiling 的 UB 预算若不预留这部分，kernel 端持久化窗口将溢出。host/kernel 的 UB 对账（预留字节 == 注册 TBuf 字节）是此类扩展的编译与正确性前提；I/O cast 边界（提升 + 真 abs、wrap-cast 缩窄）必须与原始路径逐字一致以保持位精确。",
  "related_anti_patterns": [],
  "risks": [
    "host 预留与 kernel TBuf 不对账导致 UB 溢出或 host/kernel 视图不一致",
    "提升域 abs/wrap-cast 边界改变窄 dtype 极值语义（如 -32768）导致位差异",
    "其他 dtype 分支的 tiling 数值被意外扰动",
    "每元素工作量小的 route 上，chunk 同步开销占比更高，早退收益可能被稀释"
  ],
  "slug": "promoted-domain-ub-reservation-early-exit",
  "summary": "把分块全 lane 早退扩展到 dtype 提升计算域：提升域 A/B 在 chunk 间持久化需要 2x 原生宽度的 UB 窗口，必须由 host tiling 在 UB 预算中预留对应字节并让 kernel 注册匹配 TBuf，否则只改 kernel 会超出预算；I/O 边界保持提升域真 abs 与 wrap-cast 缩窄，使早退收益落到此前因 UB 预算被排除的 dtype route。",
  "verification": {
    "correctness": [
      "全量 verify 位精确，覆盖全 dtype 域（含 -32768 真 abs 提升路径与极值 wrap）"
    ],
    "performance": [
      "目标提升域 route 中位时延按早退轮数比例下降",
      "非目标 dtype route 中位数与基准一致（tiling 未被扰动）"
    ],
    "rollback_signals": [
      "任一 verify 位精确失败",
      "host/tiling 数值被意外改变导致非目标 route 回归",
      "目标 route 无方向性收益（chunk 同步开销稀释早退收益）"
    ]
  }
}
-->

# 性能优化策略：提升域持久态早退：host tiling 为提升后中间态预留 UB 窗口

单一优化点：把分块全 lane 早退扩展到 dtype 提升计算域：提升域 A/B 在 chunk 间持久化需要 2x 原生宽度的 UB 窗口，必须由 host tiling 在 UB 预算中预留对应字节并让 kernel 注册匹配 TBuf，否则只改 kernel 会超出预算；I/O 边界保持提升域真 abs 与 wrap-cast 缩窄，使早退收益落到此前因 UB 预算被排除的 dtype route。

## 1. 原理

当计算在提升域（窄 dtype 提升到宽 dtype）执行、且机制需要在 chunk 间持久化提升后的中间态时，UB 需求是原生宽度的 2x；host tiling 的 UB 预算若不预留这部分，kernel 端持久化窗口将溢出。host/kernel 的 UB 对账（预留字节 == 注册 TBuf 字节）是此类扩展的编译与正确性前提；I/O cast 边界（提升 + 真 abs、wrap-cast 缩窄）必须与原始路径逐字一致以保持位精确。

实现机制：在 host tiling 的 simdWorkB 计算后，对目标窄 dtype 分支追加预留 2 * CeilAlign(VF_ELEMS * sizeof(提升域 dtype), 32) 字节（int16 提升 int32 时 +2048B，ubFactor 收缩 <1%），其他 dtype 分支的 tiling 完全不动；kernel 侧注册两个提升域持久化 TBuf（各 VF_ELEMS * 4B），chunk 循环直接复用原生域的分块 VF 轮体，I/O 边界（窄 dtype 加载 -> Cast 提升 + 真 abs -> 提升域 chunk -> wrap-cast 缩窄 -> 窄 dtype 存储）与原始路径逐字一致。

## 2. 性能问题模式

- 优化目标：解除'提升域中间态超出 host tiling UB 预算'对早退机制的排除，把分块早退收益扩展到 dtype 提升的窄整型 route。
- 适用数据流：把分块全 lane 早退机制扩展到 dtype 提升计算域（窄整型提升到宽整型域执行逐元素迭代，如 int16 提升 int32 计算欧几里得）的流式 elementwise route；热链仍 VEC-bound，且新机制需要在 chunk 间持久化提升后的中间态
- Feature signature：`{"bottleneck": ["vec-bound", "fixed-round-loop", "promoted-domain-ub-pressure"], "dtypes": ["int16"], "pattern": "promoted-domain-persistent-state-ub-reservation", "structure": ["dtype-promotion", "vec-iterative-loop", "host-ub-budget", "ub-persistent-state"]}`

## 3. 正确性红线

- host 预留与 kernel TBuf 不对账导致 UB 溢出或 host/kernel 视图不一致
- 提升域 abs/wrap-cast 边界改变窄 dtype 极值语义（如 -32768）导致位差异
- 其他 dtype 分支的 tiling 数值被意外扰动
- 每元素工作量小的 route 上，chunk 同步开销占比更高，早退收益可能被稀释

资源与硬件约束：

- 预留只作用于目标 dtype 分支，其他 dtype 的 tiling/ubFactor 必须逐字节不变
- host 预留与 kernel TBuf 必须精确对账，否则 UB 溢出
- 提升域真 abs（如 abs(-32768)=32768）必须在提升后、abs 之前执行以保位精确
- 缩窄出口（wrap-cast）必须与原始路径一致，覆盖全 dtype 域（含极值）

## 4. 泛化条件

- 策略作用域：op_class：broadcast

适用：

- 热链为提升域计算：窄 dtype 提升到宽 dtype 域执行，且分块早退机制需要在 chunk 间持久化提升后的中间态
- host tiling 有独立的 UB 预算（simdWorkB/ubFactor），且当前未为提升域持久态预留窗口
- kernel 与 host 能精确对账预留字节与 TBuf 注册字节
- I/O cast 边界（提升 + 真 abs、wrap-cast 缩窄）可逐字保持原始语义

不适用：

- 提升域中间态可压回原生宽度存储（无需持久化提升域状态）时不适用
- host tiling 无法单独调整（如编辑范围只允许 kernel）且无法复用现有窗口时，此机制需先解除编辑范围限制
- 非 VEC-bound route 不预期从该机制获得时延收益

## 5. 实施步骤

1. 确认热链在提升域执行且分块早退机制需要持久化提升后中间态，评估 2x 原生宽度 UB 缺口
2. 在 host tiling 中对目标 dtype 分支预留 2 * CeilAlign(VF_ELEMS * sizeof(提升域 dtype), 32) 字节，其他 dtype 分支不动
3. kernel 注册匹配的提升域持久化 TBuf，chunk 循环复用原生域分块 VF 轮体
4. 保持 I/O cast 边界逐字一致（提升 + 真 abs、wrap-cast 缩窄），跑全 dtype 域 verify（含极值）
5. 验证其他 dtype route 无 tiling/性能回归，实测调参 K 与 done 检查频率

## 6. LLM 前置问题

- 目标实现是否满足：热链为提升域计算：窄 dtype 提升到宽 dtype 域执行，且分块早退机制需要在 chunk 间持久化提升后的中间态？
- 目标实现是否满足：host tiling 有独立的 UB 预算（simdWorkB/ubFactor），且当前未为提升域持久态预留窗口？
- 目标实现是否满足：kernel 与 host 能精确对账预留字节与 TBuf 注册字节？
- 是否命中排除条件：提升域中间态可压回原生宽度存储（无需持久化提升域状态）时不适用？

## 7. 验收标准

正确性：

- 全量 verify 位精确，覆盖全 dtype 域（含 -32768 真 abs 提升路径与极值 wrap）

性能：

- 目标提升域 route 中位时延按早退轮数比例下降
- 非目标 dtype route 中位数与基准一致（tiling 未被扰动）

回滚信号：

- 任一 verify 位精确失败
- host/tiling 数值被意外改变导致非目标 route 回归
- 目标 route 无方向性收益（chunk 同步开销稀释早退收益）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gcd-20260824_045521-4a1ef3（round=2, status=accepted, case=T1(1,4,8,12,16,19), speedup=T1 int16 2.73-5.72x; T2/T3 control 保持 round-1 中位数 (<0.05% 偏差); total 4.4726）
- gcd-20260824_045521-4a1ef3（round=2, status=accepted）

## 检索卡（短卡）

动作：在host tiling的目标dtype分支按原生宽度2倍预留UB，使kernel可跨chunk持久化提升域中间态
适用：窄dtype在宽域计算，且分块早退需跨chunk持久化提升域中间态
限制：仅修改目标dtype分支，其他dtype的tiling/ubFactor逐字节不变；host与kernel须对账
范围：elementwise-arithmetic的窄整型提升分支
检索词：提升域、host tiling、kernel TBuf、UB对账、CeilAlign、分块全lane早退
机会：提升域持久态超出host的UB预算，kernel持久化窗口会溢出
代价：目标分支的持久态UB需求为原生宽度的2倍
