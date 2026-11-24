---
type: Optimization
title: elementwise batch-per-lane 的 fused row-streaming 变体（n=6,8）
description: R3 机制在 n=6/8 路由的 fused row-streaming 变体：Iter1 行 softmax-only + IterK fused col-norm/row-norm + trailing col-norm，全部 elementwise、byte-identical per-batch 值序列。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/elementwise-batch-per-lane-fused-rowstream-n6n8.md
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
      "Iter1/IterK/trailing 的融合必须保持原算法累加顺序与精度契约（byte-identical per-batch 值序列）",
      "共享文件改动需逐字保留 n=2/3/4 已验证 VF",
      "小 shape 控制 case 的亚微秒抖动按 noise-floor 记录，不否定机制"
    ],
    "excluded_conditions": [
      "n>8 或矩阵/统计量驻留不了寄存器时不适用",
      "非 VEC-bound 或 MTE 描述符地板主导时不预期收益",
      "值序列无法与 generic VF byte-identical 时不得上"
    ],
    "required_conditions": [
      "R3/R4 机制已生效且存在未覆盖的更大 n 路由（n=6,8）",
      "n=6/n=8 矩阵及迭代统计量可驻留寄存器（fused row-streaming 缓解压力）",
      "行/列归一化可拆成 Iter1 + IterK + trailing 的 elementwise 序列"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "d6ecc20f979a4ebdd873d36f303f346bdab2570aee5ba6d7952f7cc77c8c45e2",
      "decision_sha256": "5ede2e348f8828e911802d2fac981e7e7b2484eb4494469bf264e189d2f4b0fc",
      "operator_class": "vv-fusion",
      "performance_sha256": "24b674e23f464bc9f1086e1ea401f73a141863dbf47cea0ccf94ffb11fa6344d",
      "round": 5,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "6f7dfe763ca87c036adf3bc754c43819b7fb56a0f9e3bfdfe2030fb57c26923c",
      "verify_sha256": "3403953f2f60cd4d8f01ca84375289e0580b9dc8481a59a1bb77e634221b7f1a"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "low-lane-utilization",
      "per-batch-serial",
      "register-pressure"
    ],
    "dtypes": [
      "fp32"
    ],
    "hardware": [
      "ascend950",
      "dav_3510"
    ],
    "pattern": "elementwise-batch-per-lane-fused-rowstream-n6n8",
    "structure": [
      "multi-batch-normalization",
      "iterative-row-col-norm",
      "element-major-transpose",
      "row-streaming"
    ]
  },
  "generality": "op_class",
  "id": "VEC-MULTIBATCH-LANE-PACKING-FUSED-ROWSTREAM-N6N8",
  "implementation_steps": [
    "为 n=6/n=8 实现 fused row-streaming VF 对（Iter1 row-softmax-only + IterK fused + trailing col-norm）",
    "放宽 UseBatchPerLanePath() 到 hcMult∈{2,3,4,6,8}；ComputeGroup() 新增 6/8 分发",
    "bitwise round-trip（blockCount=36 描述符）+ 全量 correctness + 稳定性采集"
  ],
  "intent": "把 batch-per-lane 机制扩展到 n=6/8 路由（hcMult=6,8），消除该路由逐 batch 串行 VF 的 lane 利用与指令发射瓶颈，用 fused row-streaming 减少中间值驻留与重复扫描。",
  "mechanism": "在 mhc_sinkhorn_vf.h 新增 n=6/n=8 fused row-streaming VF 对（Iter1 row-softmax-only + IterK fused col-norm/row-norm + trailing col-norm，手写具名位置寄存器）；mhc_sinkhorn.h 把 UseBatchPerLanePath() 放宽到 hcMult∈{2,3,4,6,8}，ComputeGroup() 新增 6/8 分发（CopyInGroup/CopyOutGroup blockCount 与 combSlotBytes_ 已泛化，无需改动）。",
  "name": "elementwise batch-per-lane 的 fused row-streaming 变体（n=6,8）",
  "operator_class": "vv-fusion",
  "operator_scope": "同 VEC-MULTIBATCH-ELEMENTWISE-LANE-PACKING，但针对 hcMult∈{6,8}（n=6/n=8 矩阵）路由：Iter1 只做行 softmax、IterK 融合列归一化/行归一化、尾部再补列归一化",
  "principle": "n=6/8 矩阵比 n=4 大，完整 batch-resident 寄存器压力更高；把迭代拆成 '行 softmax 先行' + 'IterK 内融合列/行归一化' + '尾部列归一化' 的 row-streaming 形式，在保持 elementwise 归约与 batch-per-lane 打包的同时减少寄存器驻留与扫描遍数。值序列逐 batch 与 generic VF 字节一致，保证精度契约。",
  "related_anti_patterns": [],
  "risks": [
    "融合顺序改变导致精度漂移（byte-identical 验收拦截）",
    "n=6/8 寄存器压力导致 spill（需编译确认）",
    "共享文件改动波及已验证路由（control 监控）"
  ],
  "slug": "elementwise-batch-per-lane-fused-rowstream-n6n8",
  "summary": "R3 机制在 n=6/8 路由的 fused row-streaming 变体：Iter1 行 softmax-only + IterK fused col-norm/row-norm + trailing col-norm，全部 elementwise、byte-identical per-batch 值序列。case9（hcMult=6）27.674->21.850us = 1.2665x（cv 0.016 stable），incremental total_speedup 1.03，cumulative 2.6459；op_summary 确认 aiv_vec_time 24.652->18.665us、Task Duration 27.25->21.86us。Control 的 case2/8/17 亚微秒抖动按 R3/R4 先例的 noise-floor 标准记录，不是代码路径回归。",
  "verification": {
    "correctness": [
      "R5 verify 20/20 correctness_pass failed_cases=[]（含 blockCount=36 batch-column 描述符 bitwise round-trip case9：0/36864 bit mismatches，覆盖 0/-0/±inf/nan-payload/subnormal/min-normal/max-finite）"
    ],
    "performance": [
      "R5 incremental total_speedup 1.03 >= 1.02；case9 27.674->21.850us = 1.2665x（cv 0.016 stable）",
      "op_summary：aiv_vec_time 24.652->18.665us、Task Duration 27.25->21.86us",
      "cumulative total_speedup 2.6459、improved_cases=14、regressed_cases=1（case2 noise-floor）"
    ],
    "rollback_signals": [
      "bitwise A/B 差分失败",
      "寄存器 spill 或 n=2/3/4 路由回归",
      "值序列与 generic VF 不一致"
    ]
  }
}
-->

# 性能优化策略：elementwise batch-per-lane 的 fused row-streaming 变体（n=6,8）

单一优化点：R3 机制在 n=6/8 路由的 fused row-streaming 变体：Iter1 行 softmax-only + IterK fused col-norm/row-norm + trailing col-norm，全部 elementwise、byte-identical per-batch 值序列。case9（hcMult=6）27.674->21.850us = 1.2665x（cv 0.016 stable），incremental total_speedup 1.03，cumulative 2.6459；op_summary 确认 aiv_vec_time 24.652->18.665us、Task Duration 27.25->21.86us。Control 的 case2/8/17 亚微秒抖动按 R3/R4 先例的 noise-floor 标准记录，不是代码路径回归。

## 1. 原理

n=6/8 矩阵比 n=4 大，完整 batch-resident 寄存器压力更高；把迭代拆成 '行 softmax 先行' + 'IterK 内融合列/行归一化' + '尾部列归一化' 的 row-streaming 形式，在保持 elementwise 归约与 batch-per-lane 打包的同时减少寄存器驻留与扫描遍数。值序列逐 batch 与 generic VF 字节一致，保证精度契约。

实现机制：在 mhc_sinkhorn_vf.h 新增 n=6/n=8 fused row-streaming VF 对（Iter1 row-softmax-only + IterK fused col-norm/row-norm + trailing col-norm，手写具名位置寄存器）；mhc_sinkhorn.h 把 UseBatchPerLanePath() 放宽到 hcMult∈{2,3,4,6,8}，ComputeGroup() 新增 6/8 分发（CopyInGroup/CopyOutGroup blockCount 与 combSlotBytes_ 已泛化，无需改动）。

## 2. 性能问题模式

- 优化目标：把 batch-per-lane 机制扩展到 n=6/8 路由（hcMult=6,8），消除该路由逐 batch 串行 VF 的 lane 利用与指令发射瓶颈，用 fused row-streaming 减少中间值驻留与重复扫描。
- 适用数据流：同 VEC-MULTIBATCH-ELEMENTWISE-LANE-PACKING，但针对 hcMult∈{6,8}（n=6/n=8 矩阵）路由：Iter1 只做行 softmax、IterK 融合列归一化/行归一化、尾部再补列归一化
- Feature signature：`{"bottleneck": ["vec-bound", "low-lane-utilization", "per-batch-serial", "register-pressure"], "dtypes": ["fp32"], "hardware": ["ascend950", "dav_3510"], "pattern": "elementwise-batch-per-lane-fused-rowstream-n6n8", "structure": ["multi-batch-normalization", "iterative-row-col-norm", "element-major-transpose", "row-streaming"]}`

## 3. 正确性红线

- 融合顺序改变导致精度漂移（byte-identical 验收拦截）
- n=6/8 寄存器压力导致 spill（需编译确认）
- 共享文件改动波及已验证路由（control 监控）

资源与硬件约束：

- Iter1/IterK/trailing 的融合必须保持原算法累加顺序与精度契约（byte-identical per-batch 值序列）
- 共享文件改动需逐字保留 n=2/3/4 已验证 VF
- 小 shape 控制 case 的亚微秒抖动按 noise-floor 记录，不否定机制

## 4. 泛化条件

- 策略作用域：op_class：vv-fusion

适用：

- R3/R4 机制已生效且存在未覆盖的更大 n 路由（n=6,8）
- n=6/n=8 矩阵及迭代统计量可驻留寄存器（fused row-streaming 缓解压力）
- 行/列归一化可拆成 Iter1 + IterK + trailing 的 elementwise 序列

不适用：

- n>8 或矩阵/统计量驻留不了寄存器时不适用
- 非 VEC-bound 或 MTE 描述符地板主导时不预期收益
- 值序列无法与 generic VF byte-identical 时不得上

## 5. 实施步骤

1. 为 n=6/n=8 实现 fused row-streaming VF 对（Iter1 row-softmax-only + IterK fused + trailing col-norm）
2. 放宽 UseBatchPerLanePath() 到 hcMult∈{2,3,4,6,8}；ComputeGroup() 新增 6/8 分发
3. bitwise round-trip（blockCount=36 描述符）+ 全量 correctness + 稳定性采集

## 6. LLM 前置问题

- 目标实现是否满足：R3/R4 机制已生效且存在未覆盖的更大 n 路由（n=6,8）？
- 目标实现是否满足：n=6/n=8 矩阵及迭代统计量可驻留寄存器（fused row-streaming 缓解压力）？
- 目标实现是否满足：行/列归一化可拆成 Iter1 + IterK + trailing 的 elementwise 序列？
- 是否命中排除条件：n>8 或矩阵/统计量驻留不了寄存器时不适用？

## 7. 验收标准

正确性：

- R5 verify 20/20 correctness_pass failed_cases=[]（含 blockCount=36 batch-column 描述符 bitwise round-trip case9：0/36864 bit mismatches，覆盖 0/-0/±inf/nan-payload/subnormal/min-normal/max-finite）

性能：

- R5 incremental total_speedup 1.03 >= 1.02；case9 27.674->21.850us = 1.2665x（cv 0.016 stable）
- op_summary：aiv_vec_time 24.652->18.665us、Task Duration 27.25->21.86us
- cumulative total_speedup 2.6459、improved_cases=14、regressed_cases=1（case2 noise-floor）

回滚信号：

- bitwise A/B 差分失败
- 寄存器 spill 或 n=2/3/4 路由回归
- 值序列与 generic VF 不一致

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- mhc_sinkhorn-20260831_151225-9b5adb（round=5, status=accepted）

## 检索卡（短卡）

动作：把 n=6/8 路由迭代拆为 Iter1 行 softmax-only + IterK fused 列/行归一化 + trailing 列归一化
适用：R3/R4 batch-per-lane 已生效且存在未覆盖的 n=6,8 路由，n×n 矩阵与统计量可驻留寄存器
限制：值序列须与 generic VF byte-identical；共享文件须保留 n=2/3/4 已验证 VF
范围：vv-fusion 的 multi-batch 迭代行/列归一化（n=6,8）
检索词：fused row-streaming、hcMult、blockCount、具名位置寄存器、byte-identical
机会：n=6/8 路由逐 batch 串行 VF 的 lane 利用与发射瓶颈
代价：n=6/8 寄存器压力高可能 spill；共享文件改动波及已验证路由
