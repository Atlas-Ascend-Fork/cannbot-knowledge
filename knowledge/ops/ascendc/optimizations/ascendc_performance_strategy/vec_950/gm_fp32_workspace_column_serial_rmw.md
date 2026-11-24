---
type: Optimization
title: fp add/multiply 大足迹的 GM fp32-workspace 列独占串行累加
description: 预分配 numel×4B 的 fp32 GM workspace，把大足迹 fp add/multiply 的散射归约改为列独占、列内 j 升序的串行非原子 RMW，替代 UB D/K-split 路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/gm-fp32-workspace-column-serial-rmw.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "必须预留 numel×4B fp32 workspace，host tiling 与 GetWorkspaceSize 使用同一 gmWsEnabled 判据",
      "Pass1/Pass2 之间与 Pass2/Pass3 之间必须执行 threadfence + SyncAll + asc_dcci_entire，缺少任一环节会静默丢更新",
      "超大 shape 的 workspace 可能撞上预算上限（本 run 已验证约 268MB 量级）"
    ],
    "excluded_conditions": [
      "update/amin/amax 以及 int32/int64 add/multiply（无 golden fp32 累加语义）不使能该路径",
      "SplitCallsPerRow<24 或列独占不可满足的 case 不走该路径（收益不足以覆盖 workspace 分配/初始化成本）",
      "超大规模 shape 使 numel×4B workspace 分配失败时禁止启用"
    ],
    "required_conditions": [
      "scatter reduce 模式为 add 或 multiply，data dtype 为 fp16/bf16/fp32",
      "host 能按列独占切分，使每个输出列在整个归约期间只被一个核持有（本实现以 SplitCallsPerRow>=24 为判据）",
      "列内以 j 升序串行累积到 fp32 workspace，能与 golden acc_type=float 的累加顺序逐位一致",
      "GetWorkspaceSize 能预留 numel×4B 的 fp32 workspace 且不超预算"
    ]
  },
  "classification": "validated_strategy",
  "duplicate": {
    "existing_strategy_ids": [
      "S1-GmAddWs"
    ],
    "reason": "共享『预分配 fp32 GM workspace 归约散射更新』的原理，但本策略以列独占 + 列内 j 升序串行非原子 RMW 替代原子加，消除原子落点顺序不确定性，并把适用范围扩展到 fp32 add 与 fp16/bf16/fp32 multiply。",
    "relation": "variant"
  },
  "evidence": [
    {
      "comparison_sha256": "1a8cde69066f83e0adb6be3598aba3cf76ff6d5a735178aef0b9d0c61b602af2",
      "decision_sha256": "db70b8ba2e4652d30bb6ec4db66326be93a72b5d168de6309ff18ee2a5e3e7a8",
      "operator_class": "scatter-update",
      "performance_sha256": "88c8d6fd3bcdafc7cd9f7021169a8c65ae9dbd0ba0be255114edc4121fb1595a",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "0ce8d1bb6d146f8308542ca017fd79b5c8beded2490005a4c771036640571df7",
      "verify_sha256": "aba5579f104d2f2c8bf623094330628402563867f989062d966a93efc13562e4"
    },
    {
      "operator_class": "scatter-update",
      "precision": "20/20 PASS",
      "round": 3,
      "run_id": "<run-id>",
      "speedup": "incremental 1.3798x; case4 1.2552x, case5 2.5475x; cumulative 1.7086",
      "status": "accepted"
    },
    {
      "comparison_sha256": "d857ebcf74f3b434528435a4b656a23918c39bdb52db17da9871ce868fbc8d4d",
      "decision_sha256": "80763292b023ad264b356e3792e9b3c87e9af69a9a46a36c3ee52395374a2883",
      "operator_class": "scatter-update",
      "performance_sha256": "37217bc3cdcacb5df48cf5aa315560b3f29301a119221af3a83485f7ba0d5d79",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "aafe32e19c2a09127dfbf911ba0b503b40bb26f7ad2560997d09eb9592616b05",
      "verify_sha256": "fe3e1a5020fa18fa1ae0b3db655551dbd7bbef7ef0b8efa3416a0e9a336a2f8c"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "dk-split",
      "per-vf-dispatch",
      "pipe-all-barrier",
      "redundant-refetch"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "gm-ws-column-serial-rmw",
    "reduce_mode": "add-multiply",
    "structure": [
      "gm-workspace",
      "column-exclusive",
      "serial-rmw",
      "non-atomic",
      "j-ascending"
    ]
  },
  "generality": "op_class",
  "id": "SCATTER-GM-FP32-WS-COLUMN-SERIAL-RMW",
  "implementation_steps": [
    "host 判定 fp16/bf16/fp32 add/multiply 且 SplitCallsPerRow>=24，使能 gmWsEnabled 并在 GetWorkspaceSize 预留 numel×4B fp32 workspace",
    "Pass1：SIMT grid-stride 将 data 加宽复制到 fp32 workspace 作为累加初值",
    "执行 asc_threadfence + SyncAll + asc_dcci_entire 保证 Pass1 写对各核可见",
    "Pass2：SIMT 按列独占持有，列内以 j 升序对 ws 做串行非原子 RMW（读旧值→加/乘更新→写回）",
    "再次执行 asc_threadfence + SyncAll + asc_dcci_entire，再进入 Pass3 将 ws 单次舍回输出 dtype 写 y",
    "对不满足判据的 case 保留原 T1/T2/GM 路径，并在共享 entry/struct 改动后对全量 case 做正确性回归"
  ],
  "intent": "消除大足迹 fp add/multiply 在 UB 路径触发 D/K-split 后的固定开销（per-VF dispatch、冗余 idx/upd 重搬、逐 VF PIPE_ALL 屏障、标量 remap），同时保证累加顺序与 golden 的 acc_type=float 逐位一致。",
  "mechanism": "host 对 fp16/bf16/fp32 的 add/multiply 且 SplitCallsPerRow>=24（镜像 T1/T2 D/K-split 足迹搜索得到的最小 split 调用次数）的 case 使能 gm-ws；GetWorkspaceSize 对所有 fp add/multiply 预分配 numel×4B fp32 workspace（未使能时 kernel 不消费，over-allocate 无害）。kernel 三段式：Pass1 SIMT grid-stride 将 data 加宽复制为 fp32 ws 初值 → asc_threadfence + SyncAll + asc_dcci_entire → Pass2 SIMT 按列独占、列内 j 升序做串行非原子 RMW（列间目标位不相交，无跨线程竞态）→ asc_threadfence + SyncAll + asc_dcci_entire → Pass3 SIMT 将 ws 单次舍回输出 dtype 写 y。SplitCallsPerRow<24、update/amin/amax 或 int32/int64 add/multiply 走原 T1/T2/GM 路径。",
  "name": "fp add/multiply 大足迹的 GM fp32-workspace 列独占串行累加",
  "operator_class": "scatter-update",
  "operator_scope": "存在重复索引、归约模式为 add 或 multiply、输出为 fp16/bf16/fp32，且大足迹触发 UB 路径 D/K-split 退化的 scatter-update 数据流",
  "principle": "当每个输出列可被单一核/线程在整个归约期间独占持有、且列内更新按 j 升序串行累积到 fp32 workspace 时，非原子 RMW 与原子加产生相同的累加结果与顺序，却完全不需要原子指令、冲突重试和落点顺序不确定性；fp32 中间累加 + 末尾一次舍回既能匹配 golden 的 fp32 累加精度，又能消除低精度多次舍入。",
  "related_anti_patterns": [
    "dk-split-scalar-address-remap",
    "simt-write-mte-read-visibility-gap"
  ],
  "risks": [
    "Pass1/Pass2 与 Pass2/Pass3 之间缺少 threadfence、核间同步或 cache 失效，会静默丢失更新",
    "超大 shape 的 numel×4B workspace 可能超预算，分配失败是回滚信号",
    "列独占判据（SplitCallsPerRow>=24）与真实 split 足迹不匹配时会误路由，需逐 case 验证边界",
    "workspace over-allocate 对未使能 case 无害，但 UB 回退 case 可能出现噪音级波动，不应过度解读"
  ],
  "slug": "gm-fp32-workspace-column-serial-rmw",
  "summary": "预分配 numel×4B 的 fp32 GM workspace，把大足迹 fp add/multiply 的散射归约改为列独占、列内 j 升序的串行非原子 RMW，替代 UB D/K-split 路径。",
  "verification": {
    "correctness": [
      "全 20/20 例 PASS（kernel_hash 3be8eec0ec7adbf8），正确性范围保守扩展到共享 entry/struct 触达的全部 case",
      "逐列 j 升序 fp32 累加与 golden acc_type=float 顺序一致，规避原子 add 落点顺序在相消点超阈"
    ],
    "performance": [
      "目标 case（大足迹 fp add/multiply）实测大幅提速，目标路径聚合约 14.4x",
      "控制路径（GM 路径 update/amin/amax/int32-add 与 UB 回退 fp add/multiply）无稳定回归（0.9936x–1.0037x）",
      "所有 round 性能 case 采样稳定（cv<0.03、relative_mad<0.02、retry_recommended=false）"
    ],
    "rollback_signals": [
      "出现更新丢失、MERE/MARE 超阈、workspace 分配失败、非目标模式误路由或控制路径稳定回归时回退"
    ]
  }
}
-->

# 性能优化策略：fp add/multiply 大足迹的 GM fp32-workspace 列独占串行累加

单一优化点：预分配 numel×4B 的 fp32 GM workspace，把大足迹 fp add/multiply 的散射归约改为列独占、列内 j 升序的串行非原子 RMW，替代 UB D/K-split 路径。

## 1. 原理

当每个输出列可被单一核/线程在整个归约期间独占持有、且列内更新按 j 升序串行累积到 fp32 workspace 时，非原子 RMW 与原子加产生相同的累加结果与顺序，却完全不需要原子指令、冲突重试和落点顺序不确定性；fp32 中间累加 + 末尾一次舍回既能匹配 golden 的 fp32 累加精度，又能消除低精度多次舍入。

实现机制：host 对 fp16/bf16/fp32 的 add/multiply 且 SplitCallsPerRow>=24（镜像 T1/T2 D/K-split 足迹搜索得到的最小 split 调用次数）的 case 使能 gm-ws；GetWorkspaceSize 对所有 fp add/multiply 预分配 numel×4B fp32 workspace（未使能时 kernel 不消费，over-allocate 无害）。kernel 三段式：Pass1 SIMT grid-stride 将 data 加宽复制为 fp32 ws 初值 → asc_threadfence + SyncAll + asc_dcci_entire → Pass2 SIMT 按列独占、列内 j 升序做串行非原子 RMW（列间目标位不相交，无跨线程竞态）→ asc_threadfence + SyncAll + asc_dcci_entire → Pass3 SIMT 将 ws 单次舍回输出 dtype 写 y。SplitCallsPerRow<24、update/amin/amax 或 int32/int64 add/multiply 走原 T1/T2/GM 路径。

## 2. 性能问题模式

- 优化目标：消除大足迹 fp add/multiply 在 UB 路径触发 D/K-split 后的固定开销（per-VF dispatch、冗余 idx/upd 重搬、逐 VF PIPE_ALL 屏障、标量 remap），同时保证累加顺序与 golden 的 acc_type=float 逐位一致。
- 适用数据流：存在重复索引、归约模式为 add 或 multiply、输出为 fp16/bf16/fp32，且大足迹触发 UB 路径 D/K-split 退化的 scatter-update 数据流
- Feature signature：`{"bottleneck": ["dk-split", "per-vf-dispatch", "pipe-all-barrier", "redundant-refetch"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "gm-ws-column-serial-rmw", "reduce_mode": "add-multiply", "structure": ["gm-workspace", "column-exclusive", "serial-rmw", "non-atomic", "j-ascending"]}`

## 3. 正确性红线

- Pass1/Pass2 与 Pass2/Pass3 之间缺少 threadfence、核间同步或 cache 失效，会静默丢失更新
- 超大 shape 的 numel×4B workspace 可能超预算，分配失败是回滚信号
- 列独占判据（SplitCallsPerRow>=24）与真实 split 足迹不匹配时会误路由，需逐 case 验证边界
- workspace over-allocate 对未使能 case 无害，但 UB 回退 case 可能出现噪音级波动，不应过度解读

资源与硬件约束：

- 必须预留 numel×4B fp32 workspace，host tiling 与 GetWorkspaceSize 使用同一 gmWsEnabled 判据
- Pass1/Pass2 之间与 Pass2/Pass3 之间必须执行 threadfence + SyncAll + asc_dcci_entire，缺少任一环节会静默丢更新
- 超大 shape 的 workspace 可能撞上预算上限（本 run 已验证约 268MB 量级）

## 4. 泛化条件

- 策略作用域：op_class：scatter-update

适用：

- scatter reduce 模式为 add 或 multiply，data dtype 为 fp16/bf16/fp32
- host 能按列独占切分，使每个输出列在整个归约期间只被一个核持有（本实现以 SplitCallsPerRow>=24 为判据）
- 列内以 j 升序串行累积到 fp32 workspace，能与 golden acc_type=float 的累加顺序逐位一致
- GetWorkspaceSize 能预留 numel×4B 的 fp32 workspace 且不超预算

不适用：

- update/amin/amax 以及 int32/int64 add/multiply（无 golden fp32 累加语义）不使能该路径
- SplitCallsPerRow<24 或列独占不可满足的 case 不走该路径（收益不足以覆盖 workspace 分配/初始化成本）
- 超大规模 shape 使 numel×4B workspace 分配失败时禁止启用

## 5. 实施步骤

1. host 判定 fp16/bf16/fp32 add/multiply 且 SplitCallsPerRow>=24，使能 gmWsEnabled 并在 GetWorkspaceSize 预留 numel×4B fp32 workspace
2. Pass1：SIMT grid-stride 将 data 加宽复制到 fp32 workspace 作为累加初值
3. 执行 asc_threadfence + SyncAll + asc_dcci_entire 保证 Pass1 写对各核可见
4. Pass2：SIMT 按列独占持有，列内以 j 升序对 ws 做串行非原子 RMW（读旧值→加/乘更新→写回）
5. 再次执行 asc_threadfence + SyncAll + asc_dcci_entire，再进入 Pass3 将 ws 单次舍回输出 dtype 写 y
6. 对不满足判据的 case 保留原 T1/T2/GM 路径，并在共享 entry/struct 改动后对全量 case 做正确性回归

## 6. LLM 前置问题

- 目标实现是否满足：scatter reduce 模式为 add 或 multiply，data dtype 为 fp16/bf16/fp32？
- 目标实现是否满足：host 能按列独占切分，使每个输出列在整个归约期间只被一个核持有（本实现以 SplitCallsPerRow>=24 为判据）？
- 目标实现是否满足：列内以 j 升序串行累积到 fp32 workspace，能与 golden acc_type=float 的累加顺序逐位一致？
- 是否命中排除条件：update/amin/amax 以及 int32/int64 add/multiply（无 golden fp32 累加语义）不使能该路径？

## 7. 验收标准

正确性：

- 全 20/20 例 PASS（kernel_hash 3be8eec0ec7adbf8），正确性范围保守扩展到共享 entry/struct 触达的全部 case
- 逐列 j 升序 fp32 累加与 golden acc_type=float 顺序一致，规避原子 add 落点顺序在相消点超阈

性能：

- 目标 case（大足迹 fp add/multiply）实测大幅提速，目标路径聚合约 14.4x
- 控制路径（GM 路径 update/amin/amax/int32-add 与 UB 回退 fp add/multiply）无稳定回归（0.9936x–1.0037x）
- 所有 round 性能 case 采样稳定（cv<0.03、relative_mad<0.02、retry_recommended=false）

回滚信号：

- 出现更新丢失、MERE/MARE 超阈、workspace 分配失败、非目标模式误路由或控制路径稳定回归时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：dk-split-scalar-address-remap, simt-write-mte-read-visibility-gap

- scatter-20260827_060939-66a39a（round=1, status=accepted）
- scatter-20260830_063304-b55c13（round=3, status=accepted, speedup=incremental 1.3798x; case4 1.2552x, case5 2.5475x; cumulative 1.7086）
- scatter-20260830_063304-b55c13（round=3, status=accepted）

## 检索卡（短卡）

动作：在列独占前提下按j升序非原子RMW到fp32 workspace，避免原子指令及冲突重试
适用：输出列可由单核/线程全程独占，列内按 j 升序串行累积；适用于 fp16/bf16/fp32 的 add 或 multiply
限制：预留numel×4B工作区且host口径一致；阶段间须以threadfence、核间同步及cache失效保证可见性
范围：scatter-reduce 的 fp16/bf16/fp32 add/multiply
检索词：fp32 workspace、非原子 RMW、D/K-split、scatter-reduce、列独占
机会：大足迹 fp add/multiply 在 UB 路径触发 D/K-split 后仍有固定开销
代价：额外占用 numel×4B workspace
