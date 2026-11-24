---
type: Optimization
title: 量化 cast 链在 int8 容差内的压缩
description: 把 f32→i32→f32→half→int8 压成 f32→half(RINT)→int8(SAT,RINT)，用 NaN/Inf/±128 验证。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/cast-chain-fusion-int8-tolerance.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "schema_version": 2,
  "id": "F9",
  "slug": "cast-chain-fusion-int8-tolerance",
  "name": "量化 cast 链在 int8 容差内的压缩",
  "summary": "把 f32→i32→f32→half→int8 压成 f32→half(RINT)→int8(SAT,RINT)，用 NaN/Inf/±128 验证。",
  "intent": "减少量化尾部的 VEC 指令数",
  "mechanism": "在官方 int8 容差（abs diff ≤1）内，把 f32→i32→f32→half→int8 压成 f32→half(RINT)→int8(SAT,RINT)；半精度 RINT 在 [-128,127] 误差 ≤1，饱和用 CAST 的 SAT；必须覆盖 NaN/Inf/±128/全 0。",
  "principle": "量化尾部的多条 cast 是纯指令开销；只要最终舍入与饱和在容差内，中间整数往返可以省略。",
  "operator_scope": "动态量化/饱和 cast 链，输出 int8",
  "operator_class": "",
  "op": "seed",
  "applicability": {
    "required_conditions": [
      "官方 int8 容差允许 ±1",
      "饱和语义可保持",
      "覆盖 NaN/Inf/边界"
    ],
    "excluded_conditions": [
      "要求位级一致的 golden",
      "输出可能超 int8 且不能饱和",
      "中间 i32 有非舍入用途"
    ],
    "constraints": [
      "必须保留 SAT",
      "必须测 NaN/Inf/±128",
      "记录 MERE/MARE"
    ]
  },
  "applicability_boundary": "",
  "feature_signature": {
    "bottleneck": [
      "vec-instruction-count"
    ],
    "pattern": "quantization-tail",
    "reduce_mode": "cast",
    "structure": [
      "cast-fusion",
      "sat",
      "rint"
    ],
    "dtypes": [
      "int8"
    ]
  },
  "implementation_steps": [
    "确认官方 int8 容差与 golden 舍入规则",
    "用 half(RINT) 替代 f32→i32→f32→half",
    "用 int8(SAT,RINT) 收尾",
    "覆盖 NaN/Inf/±128/全 0",
    "全量精度 + 关键 case A/B"
  ],
  "verification": {
    "correctness": [
      "20/20",
      "NaN/Inf/边界正确",
      "max|diff| ≤1"
    ],
    "performance": [
      "相对基线有可测提升；具体数值不在卡内给出",
      "关键 shape 不回归"
    ],
    "rollback_signals": [
      "max|diff|>1 或 NaN/Inf 失败时回退原 cast 链"
    ]
  },
  "risks": [
    "舍入规则差异",
    "半精度边界",
    "饱和未保留"
  ],
  "gain": "已验证：该机制在目标 A5 算子族上有效，精度 20/20。",
  "generality": "common",
  "classification": "validated_strategy",
  "created": "2026-11-11",
  "evidence": [
    {
      "run_id": "<run-id>",
      "operator_class": "dynamic-quantization",
      "status": "accepted",
      "speedup": "validated",
      "precision": "20/20 PASS"
    }
  ],
  "related_anti_patterns": [
    "single-pass-fused-statistics-chain"
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

# 性能优化策略：量化 cast 链在 int8 容差内的压缩

单一优化点：把 f32→i32→f32→half→int8 压成 f32→half(RINT)→int8(SAT,RINT)，用 NaN/Inf/±128 验证。

## 1. 原理

量化尾部的多条 cast 是纯指令开销；只要最终舍入与饱和在容差内，中间整数往返可以省略。

实现机制：在官方 int8 容差（abs diff ≤1）内，把 f32→i32→f32→half→int8 压成 f32→half(RINT)→int8(SAT,RINT)；半精度 RINT 在 [-128,127] 误差 ≤1，饱和用 CAST 的 SAT；必须覆盖 NaN/Inf/±128/全 0。

## 2. 性能问题模式

- 优化目标：减少量化尾部的 VEC 指令数
- 适用数据流：动态量化/饱和 cast 链，输出 int8
- Feature signature：`{"bottleneck": ["vec-instruction-count"], "pattern": "quantization-tail", "reduce_mode": "cast", "structure": ["cast-fusion", "sat", "rint"], "dtypes": ["int8"]}`

## 3. 正确性红线

- 20/20
- NaN/Inf/边界正确
- max|diff| ≤1

资源与硬件约束：

- 必须保留 SAT
- 必须测 NaN/Inf/±128
- 记录 MERE/MARE

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 官方 int8 容差允许 ±1
- 饱和语义可保持
- 覆盖 NaN/Inf/边界

不适用：

- 要求位级一致的 golden
- 输出可能超 int8 且不能饱和
- 中间 i32 有非舍入用途

## 5. 实施步骤

1. 确认官方 int8 容差与 golden 舍入规则
2. 用 half(RINT) 替代 f32→i32→f32→half
3. 用 int8(SAT,RINT) 收尾
4. 覆盖 NaN/Inf/±128/全 0
5. 全量精度 + 关键 case A/B

## 6. LLM 前置问题

- 目标实现是否满足：官方 int8 容差允许 ±1？
- 目标实现是否满足：饱和语义可保持？
- 目标实现是否满足：覆盖 NaN/Inf/边界？
- 是否命中排除条件：要求位级一致的 golden？
- 是否命中排除条件：输出可能超 int8 且不能饱和？
- 是否命中排除条件：中间 i32 有非舍入用途？

## 7. 验收标准

正确性：

- 20/20
- NaN/Inf/边界正确
- max|diff| ≤1

性能：

- 相对基线有可测提升；具体数值不在卡内给出
- 关键 shape 不回归

回滚信号：

- max|diff|>1 或 NaN/Inf 失败时回退原 cast 链

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related strategies：single-pass-fused-statistics-chain

- v3-cardonly-cast-20261111-01（status=accepted, operator_class=dynamic-quantization, speedup=validated, precision=20/20 PASS）

## 检索卡（短卡）

动作：int8量化尾把f32→i32→f32→half→int8+2clamp压成f32→half(RINT)→int8(SAT,RINT)，用NaN/Inf/±128边界验证。
适用：动态量化/饱和cast链，输出int8。
限制：半精度RINT在[-128,127]误差≤1；必须保留SAT；NaN/Inf/±128覆盖。
范围：量化cast链的指令压缩。
检索词：cast链、RINT、SAT、int8容差、NaN/Inf、饱和。
机会：cast链压缩在目标shape上有效，精度不变。
代价：容差内近似；golden舍入规则要核对。
