---
type: Optimization
title: elementwise batch-per-lane 泛化到 n=2,3 路由（batch-column 描述符 blockCount=n²）
description: 把 batch-per-lane VF 泛化到 n=2/3 路由，blockCount 泛化为 hcMult²，UseBatchPerLanePath 放宽到 {2,3,4}。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/elementwise-batch-per-lane-n2n3-route.md
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
      "新增 VF 必须 byte-identical per-batch 值序列（bitwise round-trip 验收，覆盖 0/-0/±inf/nan/subnormal）",
      "batch-column 描述符 blockCount 必须随 hcMult 泛化，避免 n=2 专属 fallback",
      "小 shape 控制 case 的亚微秒抖动按 noise-floor 处理，不否定机制"
    ],
    "excluded_conditions": [
      "n=1 或 n 覆盖不全（本 run 未验证 n=1/5/7 路由）",
      "非 VEC-bound 或矩阵驻留不了寄存器时不适用",
      "目标 case 已命中更快的专用路径时收益有限"
    ],
    "required_conditions": [
      "R3 机制已生效（elementwise batch-per-lane）且存在未覆盖的更小 n 路由（n=2,3）",
      "n=2/n=3 矩阵可整体驻留寄存器，行/列归约可拆成 elementwise 序列",
      "共享 kernel 文件中对模板专用分支的改动，其它路由有逐字保留的回退路径"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "b991ffc6b0309cde264577cd574fb137b8e1f632bcfc268331a42288b4282861",
      "decision_sha256": "ef313acf4640a5d6d2f9db3d505ea94300c6cd7bc59ec2c6749a17fe93c15e5e",
      "operator_class": "vv-fusion",
      "performance_sha256": "843aee7bf7338520b755ac9ddd7a79a48ab30cfac395ad56e4a3e0d9bcf916f7",
      "round": 4,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "869b41bec7bd4939b3bf984e49650ccbb13235a45ea240093f13e86470eabdb6",
      "verify_sha256": "918eeaea3276806ce600db26c54a88e642df74cba77dfc980b967b05dbd00236"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "low-lane-utilization",
      "per-batch-serial"
    ],
    "dtypes": [
      "fp32"
    ],
    "hardware": [
      "ascend950",
      "dav_3510"
    ],
    "pattern": "elementwise-batch-per-lane-n2n3-route",
    "structure": [
      "multi-batch-normalization",
      "iterative-row-col-norm",
      "element-major-transpose"
    ]
  },
  "generality": "op_class",
  "id": "VEC-MULTIBATCH-LANE-PACKING-N2N3-ROUTE",
  "implementation_steps": [
    "为 n=2/n=3 手写具名寄存器 VF 对（Iter1/IterK）",
    "放宽 UseBatchPerLanePath() 到 hcMult∈{2,3,4}；泛化 CopyInGroup/CopyOutGroup blockCount",
    "ComputeGroup() 新增 n=2/n=3 分发；bitwise round-trip + 全量 correctness + 官方 spot check"
  ],
  "intent": "把 R3 已验证的 batch-per-lane 机制扩展到更小的 batch 规格（n=2,3），消除 R3_generic_ge64 路由上逐 batch 串行 VF 的低 lane 利用率与 MTE3 描述符开销。",
  "mechanism": "在 mhc_sinkhorn_vf.h 新增 n=2/n=3 elementwise batch-per-lane VF 对（手写具名寄存器、byte-identical per-batch 值序列）；mhc_sinkhorn.h 把 UseBatchPerLanePath() 放宽到 hcMult∈{2,3,4}，CopyInGroup/CopyOutGroup blockCount 泛化为 hcMult_*hcMult_，ComputeGroup() 分发到新 VF 对；n=4/resident4/generic VF 逐字保留。",
  "name": "elementwise batch-per-lane 泛化到 n=2,3 路由（batch-column 描述符 blockCount=n²）",
  "operator_class": "vv-fusion",
  "operator_scope": "同 VEC-MULTIBATCH-ELEMENTWISE-LANE-PACKING，但覆盖 R3_generic_ge64 路由中 hcMult∈{2,3}（n=2/n=3 矩阵）的小 batch 规格；共享 kernel 文件中模板专用改动，n=4 等其它路由不受影响",
  "principle": "同一 elementwise batch-per-lane 原理（G 个 batch 同位置元素进一条 64-lane 指令、elementwise 归约、batch-column 描述符）对不同 n 只需更换寄存器命名与描述符 blockCount=n²；n=2/3 的路由此前未命中 R3 的 n=4 专用路径，仍然逐 batch 串行，因此收益显著（VEC collapse：case7 aiv_vec 20.7->1.6us、case8 22.2->2.1us）。",
  "related_anti_patterns": [],
  "risks": [
    "寄存器命名/值序列与 generic VF 不一致导致精度漂移",
    "描述符 blockCount 未泛化导致 n=2 走 fallback（收益丢失）",
    "共享文件改动波及 n=4 等已验证路由（需逐字保留 + control 监控）"
  ],
  "slug": "elementwise-batch-per-lane-n2n3-route",
  "summary": "把 R3 的 elementwise batch-per-lane VF 泛化到 n=2 与 n=3：新增手写具名寄存器的 ComputeSinkhornIter1/IterKBatchPerLane{2,3}VF 对，UseBatchPerLanePath() 放宽到 hcMult∈{2,3,4}，CopyInGroup/CopyOutGroup 的 blockCount 泛化为 hcMult_*hcMult_。case7/8 提升 3.85x/4.42x（aggregate 4.12x），cumulative total_speedup 2.5651、regressed_cases=0；case7 官方路径可复现（claimed 6.24 vs official 5.9us）。控制 case20 的 0.9305 增量抖动记为 microkernel_noise_floor（NaN 输入 ~6us kernel，绝对差 +0.444us），不是代码路径回归。",
  "verification": {
    "correctness": [
      "R4 verify 20/20 correctness_pass failed_cases=[]（含 blockCount=4/9 batch-column 描述符 bitwise round-trip case7/8）",
      "round-trip 覆盖 0/-0/±inf/nan/subnormal/min-normal/max-finite"
    ],
    "performance": [
      "R4 incremental total_speedup 1.1358；case7 3.85x、case8 4.42x（aggregate 4.12x）",
      "cumulative total_speedup 2.5651、regressed_cases=0",
      "case7 official spot check：claimed 6.24 vs official 5.9us（ratio 1.0572, reproducible）",
      "case7 aiv_vec 20.7->1.6us、case8 22.2->2.1us（VEC collapse；copy-descriptor 地板 1.2-1.8us 成为关键路径）"
    ],
    "rollback_signals": [
      "bitwise A/B 差分失败",
      "n=4 等已验证路由的回归（control case）",
      "描述符 blockCount 未泛化导致回退"
    ]
  }
}
-->

# 性能优化策略：elementwise batch-per-lane 泛化到 n=2,3 路由（batch-column 描述符 blockCount=n²）

单一优化点：把 R3 的 elementwise batch-per-lane VF 泛化到 n=2 与 n=3：新增手写具名寄存器的 ComputeSinkhornIter1/IterKBatchPerLane{2,3}VF 对，UseBatchPerLanePath() 放宽到 hcMult∈{2,3,4}，CopyInGroup/CopyOutGroup 的 blockCount 泛化为 hcMult_*hcMult_。case7/8 提升 3.85x/4.42x（aggregate 4.12x），cumulative total_speedup 2.5651、regressed_cases=0；case7 官方路径可复现（claimed 6.24 vs official 5.9us）。控制 case20 的 0.9305 增量抖动记为 microkernel_noise_floor（NaN 输入 ~6us kernel，绝对差 +0.444us），不是代码路径回归。

## 1. 原理

同一 elementwise batch-per-lane 原理（G 个 batch 同位置元素进一条 64-lane 指令、elementwise 归约、batch-column 描述符）对不同 n 只需更换寄存器命名与描述符 blockCount=n²；n=2/3 的路由此前未命中 R3 的 n=4 专用路径，仍然逐 batch 串行，因此收益显著（VEC collapse：case7 aiv_vec 20.7->1.6us、case8 22.2->2.1us）。

实现机制：在 mhc_sinkhorn_vf.h 新增 n=2/n=3 elementwise batch-per-lane VF 对（手写具名寄存器、byte-identical per-batch 值序列）；mhc_sinkhorn.h 把 UseBatchPerLanePath() 放宽到 hcMult∈{2,3,4}，CopyInGroup/CopyOutGroup blockCount 泛化为 hcMult_*hcMult_，ComputeGroup() 分发到新 VF 对；n=4/resident4/generic VF 逐字保留。

## 2. 性能问题模式

- 优化目标：把 R3 已验证的 batch-per-lane 机制扩展到更小的 batch 规格（n=2,3），消除 R3_generic_ge64 路由上逐 batch 串行 VF 的低 lane 利用率与 MTE3 描述符开销。
- 适用数据流：同 VEC-MULTIBATCH-ELEMENTWISE-LANE-PACKING，但覆盖 R3_generic_ge64 路由中 hcMult∈{2,3}（n=2/n=3 矩阵）的小 batch 规格；共享 kernel 文件中模板专用改动，n=4 等其它路由不受影响
- Feature signature：`{"bottleneck": ["vec-bound", "low-lane-utilization", "per-batch-serial"], "dtypes": ["fp32"], "hardware": ["ascend950", "dav_3510"], "pattern": "elementwise-batch-per-lane-n2n3-route", "structure": ["multi-batch-normalization", "iterative-row-col-norm", "element-major-transpose"]}`

## 3. 正确性红线

- 寄存器命名/值序列与 generic VF 不一致导致精度漂移
- 描述符 blockCount 未泛化导致 n=2 走 fallback（收益丢失）
- 共享文件改动波及 n=4 等已验证路由（需逐字保留 + control 监控）

资源与硬件约束：

- 新增 VF 必须 byte-identical per-batch 值序列（bitwise round-trip 验收，覆盖 0/-0/±inf/nan/subnormal）
- batch-column 描述符 blockCount 必须随 hcMult 泛化，避免 n=2 专属 fallback
- 小 shape 控制 case 的亚微秒抖动按 noise-floor 处理，不否定机制

## 4. 泛化条件

- 策略作用域：op_class：vv-fusion

适用：

- R3 机制已生效（elementwise batch-per-lane）且存在未覆盖的更小 n 路由（n=2,3）
- n=2/n=3 矩阵可整体驻留寄存器，行/列归约可拆成 elementwise 序列
- 共享 kernel 文件中对模板专用分支的改动，其它路由有逐字保留的回退路径

不适用：

- n=1 或 n 覆盖不全（本 run 未验证 n=1/5/7 路由）
- 非 VEC-bound 或矩阵驻留不了寄存器时不适用
- 目标 case 已命中更快的专用路径时收益有限

## 5. 实施步骤

1. 为 n=2/n=3 手写具名寄存器 VF 对（Iter1/IterK）
2. 放宽 UseBatchPerLanePath() 到 hcMult∈{2,3,4}；泛化 CopyInGroup/CopyOutGroup blockCount
3. ComputeGroup() 新增 n=2/n=3 分发；bitwise round-trip + 全量 correctness + 官方 spot check

## 6. LLM 前置问题

- 目标实现是否满足：R3 机制已生效（elementwise batch-per-lane）且存在未覆盖的更小 n 路由（n=2,3）？
- 目标实现是否满足：n=2/n=3 矩阵可整体驻留寄存器，行/列归约可拆成 elementwise 序列？
- 目标实现是否满足：共享 kernel 文件中对模板专用分支的改动，其它路由有逐字保留的回退路径？
- 是否命中排除条件：n=1 或 n 覆盖不全（本 run 未验证 n=1/5/7 路由）？

## 7. 验收标准

正确性：

- R4 verify 20/20 correctness_pass failed_cases=[]（含 blockCount=4/9 batch-column 描述符 bitwise round-trip case7/8）
- round-trip 覆盖 0/-0/±inf/nan/subnormal/min-normal/max-finite

性能：

- R4 incremental total_speedup 1.1358；case7 3.85x、case8 4.42x（aggregate 4.12x）
- cumulative total_speedup 2.5651、regressed_cases=0
- case7 official spot check：claimed 6.24 vs official 5.9us（ratio 1.0572, reproducible）
- case7 aiv_vec 20.7->1.6us、case8 22.2->2.1us（VEC collapse；copy-descriptor 地板 1.2-1.8us 成为关键路径）

回滚信号：

- bitwise A/B 差分失败
- n=4 等已验证路由的回归（control case）
- 描述符 blockCount 未泛化导致回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- mhc_sinkhorn-20260831_151225-9b5adb（round=4, status=accepted）

## 检索卡（短卡）

动作：把 batch-per-lane VF 泛化到 n=2/3 路由，blockCount 泛化为 hcMult²，UseBatchPerLanePath 放宽到 {2,3,4}
适用：R3 机制已生效且存在未覆盖的更小 n 路由（n=2,3），矩阵可驻留寄存器、归约可拆成 elementwise
限制：新增 VF 须 byte-identical per-batch 值序列；blockCount 须随 hcMult 泛化
范围：vv-fusion 的 multi-batch 归一化 n=2,3 规格
检索词：byte-identical、blockCount=n²、hcMult、具名寄存器 VF、VEC collapse
机会：n=2/3 路由仍逐 batch 串行，aiv_vec 20.7->1.6us 的 collapse 空间未命中
