---
type: Optimization
title: 迭代稳态的分母 eps 省略
description: 稳态省略分母 eps，首轮保留；所有路径纳入同一开关并逐路径验证。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/steady-state-epsilon-omission.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "schema_version": 2,
  "id": "F7",
  "slug": "steady-state-epsilon-omission",
  "name": "迭代稳态的分母 eps 省略",
  "summary": "稳态省略分母 eps，首轮保留；所有路径纳入同一开关并逐路径验证。",
  "intent": "去掉稳态每轮的加法开销",
  "mechanism": "首轮分母可能接近 0，必须保留 eps；后续迭代已远离 0，可省略 Adds(eps)。把所有路径（含 2-way/tail 分支）的稳态 Adds 纳入同一开关，逐路径验证数值一致；只改头文件时必须 clean rebuild，避免测到旧二进制。",
  "principle": "稳态分母的数值下界由前一轮归一化保证，eps 主要防首轮除零；稳态省略只改变极小量。",
  "operator_scope": "多轮归一化/双随机化的稳态迭代",
  "operator_class": "",
  "op": "seed",
  "applicability": {
    "required_conditions": [
      "首轮与稳态可区分",
      "官方精度门有余量",
      "覆盖对抗输入"
    ],
    "excluded_conditions": [
      "单轮或轮次很少",
      "稳态分母可能接近 0",
      "精度门余量不足"
    ],
    "constraints": [
      "首轮不能省",
      "所有路径纳入同一开关",
      "逐路径验证数值一致",
      "头文件改动必须 clean rebuild"
    ]
  },
  "applicability_boundary": "",
  "feature_signature": {
    "bottleneck": [
      "redundant-scalar-add"
    ],
    "pattern": "iterative-normalization",
    "reduce_mode": "normalization",
    "structure": [
      "steady-state",
      "all-path-switch",
      "precision-gate"
    ],
    "dtypes": []
  },
  "implementation_steps": [
    "确认首轮/稳态路径可分离",
    "把所有路径的稳态 Adds(eps) 纳入同一开关",
    "跑全量与对抗输入，记录 MERE/MARE",
    "逐路径对比数值一致性",
    "清理 .o 后重新编译再评测"
  ],
  "verification": {
    "correctness": [
      "全量 20/20",
      "MERE/MARE 至少低于阈值一个数量级",
      "各路径数值一致"
    ],
    "performance": [
      "相对基线有可测提升；具体数值不在卡内给出",
      "关键 shape 不回归"
    ],
    "rollback_signals": [
      "精度余量不足/对抗输入失败/路径不一致时关闭"
    ]
  },
  "risks": [
    "数值近似",
    "极端输入敏感",
    "头文件不重编导致假阴性"
  ],
  "gain": "已验证：该机制在目标 A5 算子族上有效，精度 20/20。",
  "generality": "common",
  "classification": "validated_strategy",
  "created": "2026-11-11",
  "evidence": [
    {
      "run_id": "<run-id>",
      "operator_class": "iterative-normalization",
      "status": "accepted",
      "speedup": "validated",
      "precision": "20/20 PASS"
    }
  ],
  "related_anti_patterns": [
    "iterative-small-matrix-packed-layout"
  ],
  "related_seed_ids": [],
  "instance_ids": [],
  "source": "benchmark-extraction",
  "status": "validated",
  "provenance": {
    "skill": "validated-optimization-extraction-20261111"
  }
}
-->

# 性能优化策略：迭代稳态的分母 eps 省略

单一优化点：稳态省略分母 eps，首轮保留；所有路径纳入同一开关并逐路径验证。

## 1. 原理

稳态分母的数值下界由前一轮归一化保证，eps 主要防首轮除零；稳态省略只改变极小量。

实现机制：首轮分母可能接近 0，必须保留 eps；后续迭代已远离 0，可省略 Adds(eps)。把所有路径（含 2-way/tail 分支）的稳态 Adds 纳入同一开关，逐路径验证数值一致；只改头文件时必须 clean rebuild，避免测到旧二进制。

## 2. 性能问题模式

- 优化目标：去掉稳态每轮的加法开销
- 适用数据流：多轮归一化/双随机化的稳态迭代
- Feature signature：`{"bottleneck": ["redundant-scalar-add"], "pattern": "iterative-normalization", "reduce_mode": "normalization", "structure": ["steady-state", "all-path-switch", "precision-gate"], "dtypes": []}`

## 3. 正确性红线

- 全量 20/20
- MERE/MARE 至少低于阈值一个数量级
- 各路径数值一致

资源与硬件约束：

- 首轮不能省
- 所有路径纳入同一开关
- 逐路径验证数值一致
- 头文件改动必须 clean rebuild

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 首轮与稳态可区分
- 官方精度门有余量
- 覆盖对抗输入

不适用：

- 单轮或轮次很少
- 稳态分母可能接近 0
- 精度门余量不足

## 5. 实施步骤

1. 确认首轮/稳态路径可分离
2. 把所有路径的稳态 Adds(eps) 纳入同一开关
3. 跑全量与对抗输入，记录 MERE/MARE
4. 逐路径对比数值一致性
5. 清理 .o 后重新编译再评测

## 6. LLM 前置问题

- 目标实现是否满足：首轮与稳态可区分？
- 目标实现是否满足：官方精度门有余量？
- 目标实现是否满足：覆盖对抗输入？
- 是否命中排除条件：单轮或轮次很少？
- 是否命中排除条件：稳态分母可能接近 0？
- 是否命中排除条件：精度门余量不足？

## 7. 验收标准

正确性：

- 全量 20/20
- MERE/MARE 至少低于阈值一个数量级
- 各路径数值一致

性能：

- 相对基线有可测提升；具体数值不在卡内给出
- 关键 shape 不回归

回滚信号：

- 精度余量不足/对抗输入失败/路径不一致时关闭

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related strategies：iterative-small-matrix-packed-layout

- v1-blind-eps-20261111-01（status=accepted, operator_class=iterative-normalization, speedup=validated, precision=20/20 PASS）

## 检索卡（短卡）

动作：稳态迭代省略分母eps，首轮保留；把所有路径的稳态Adds(eps)纳入同一开关，逐路径验证；只改.h必须clean rebuild。
适用：多轮归一化/双随机化，稳态分母远离0。
限制：首轮不能省；必须20/20且MERE/MARE有余量；不同路径数值要一致。
范围：迭代归一化的稳态精度近似。
检索词：eps、稳态、全路径开关、逐路径验证、clean rebuild。
机会：稳态路径有效，精度在门内。
代价：数值近似；需精度门。
