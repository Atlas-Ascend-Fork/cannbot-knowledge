---
type: Optimization
title: 误差契约内的快速除法模式
description: 在精度阈值允许时将 0-ULP 除法切换为高吞吐 intrinsic 模式。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/relaxed-division-mode.md
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
      "只能选择平台文档明确支持、且误差落在算子精度阈值内的除法模式",
      "必须同时验证零、次正规数、Inf、NaN 和不同低精度转换路径"
    ],
    "excluded_conditions": [
      "要求逐位一致、严格 IEEE 舍入、0-ULP 或次正规数保真时不得降低精度模式",
      "整体已由 GM 带宽主导时切换除法模式通常没有实质收益"
    ],
    "required_conditions": [
      "热点路径包含高占比逐元素除法，且当前使用高代价精确模式",
      "算子验收允许有界相对或绝对误差，并能用全量数据验证误差",
      "目标平台存在吞吐更高的 intrinsic 除法模式"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-23",
  "evidence": [
    {
      "after_us": 33.7,
      "before_us": 170.4,
      "case": "1",
      "operator_class": "fused-composite",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/foreach_addcdiv_scalar/<run-id>/phase6_apply/final_report.md",
      "speedup": 5.06,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "high-precision-divide"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "relaxed-division-mode",
    "reduce_mode": "elementwise",
    "structure": [
      "vector-div",
      "precision-mode"
    ]
  },
  "gain": "计算受限 case_1 170.4→33.7us（5.06x），case_10 102.8→17.8us（5.79x）；带宽受限 case_5 约 1.02x。",
  "generality": "op_class",
  "id": "ELEM-DIV-001",
  "implementation_steps": [
    "用 profile 确认向量除法占据热点，并记录当前舍入、FTZ 和精度模式",
    "根据算子误差契约选择吞吐更高的 intrinsic 模式，保持零值处理等必要语义",
    "将模式切换限制在已证明可接受的 dtype 与路径，其他场景继续使用精确模式",
    "对边界数值和全量性能用例执行独立构建、精度与冷缓存复测"
  ],
  "intent": "在误差契约允许时，去掉逐元素除法的 0-ULP 精确模式成本。",
  "mechanism": "把向量 Div 从精确 0-ULP 配置切换为硬件 intrinsic 快速模式，以更高吞吐计算商；通过编译期或 tiling 分派限定适用 dtype，并保留严格精度回退。",
  "name": "误差契约内的快速除法模式",
  "op": "foreach_addcdiv_scalar",
  "operator_class": "fused-composite",
  "operator_scope": "除法占主导且允许有界数值误差的逐元素复合算术数据流",
  "principle": "精确除法模式为最坏数值条件支付显著硬件代价；若算子精度标准只要求有界误差，使用 intrinsic 模式可在不突破契约的前提下提高计算吞吐。",
  "provenance": {
    "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/foreach_addcdiv_scalar/<run-id>/phase6_apply/final_report.md"
  },
  "related_anti_patterns": [],
  "risks": [
    "极端输入的误差、FTZ 或特殊值行为可能与精确模式不同",
    "只在常规随机数据上验证会漏掉精度边界，导致隐藏回归"
  ],
  "schema_version": 2,
  "slug": "relaxed-division-mode",
  "source": "external_verified",
  "status": "applied",
  "summary": "在精度阈值允许时将 0-ULP 除法切换为高吞吐 intrinsic 模式。",
  "verification": {
    "correctness": [
      "按每个 dtype 的正式 MRE/MARE 或 ULP 阈值覆盖零、极小值、极大值、Inf、NaN 与符号组合"
    ],
    "performance": [
      "区分计算受限和带宽受限形状，确认收益来自 Div 吞吐且非目标路径无回归"
    ],
    "rollback_signals": [
      "特殊值语义改变、误差越界、目标平台模式不支持或计算受限形状没有稳定收益时回退"
    ]
  }
}
-->

# 性能优化策略：误差契约内的快速除法模式

单一优化点：在精度阈值允许时将 0-ULP 除法切换为高吞吐 intrinsic 模式。

## 1. 原理

精确除法模式为最坏数值条件支付显著硬件代价；若算子精度标准只要求有界误差，使用 intrinsic 模式可在不突破契约的前提下提高计算吞吐。

实现机制：把向量 Div 从精确 0-ULP 配置切换为硬件 intrinsic 快速模式，以更高吞吐计算商；通过编译期或 tiling 分派限定适用 dtype，并保留严格精度回退。

## 2. 性能问题模式

- 优化目标：在误差契约允许时，去掉逐元素除法的 0-ULP 精确模式成本。
- 适用数据流：除法占主导且允许有界数值误差的逐元素复合算术数据流
- Feature signature：`{"bottleneck": ["high-precision-divide"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "relaxed-division-mode", "reduce_mode": "elementwise", "structure": ["vector-div", "precision-mode"]}`

## 3. 正确性红线

- 极端输入的误差、FTZ 或特殊值行为可能与精确模式不同
- 只在常规随机数据上验证会漏掉精度边界，导致隐藏回归

资源与硬件约束：

- 只能选择平台文档明确支持、且误差落在算子精度阈值内的除法模式
- 必须同时验证零、次正规数、Inf、NaN 和不同低精度转换路径

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 热点路径包含高占比逐元素除法，且当前使用高代价精确模式
- 算子验收允许有界相对或绝对误差，并能用全量数据验证误差
- 目标平台存在吞吐更高的 intrinsic 除法模式

不适用：

- 要求逐位一致、严格 IEEE 舍入、0-ULP 或次正规数保真时不得降低精度模式
- 整体已由 GM 带宽主导时切换除法模式通常没有实质收益

## 5. 实施步骤

1. 用 profile 确认向量除法占据热点，并记录当前舍入、FTZ 和精度模式
2. 根据算子误差契约选择吞吐更高的 intrinsic 模式，保持零值处理等必要语义
3. 将模式切换限制在已证明可接受的 dtype 与路径，其他场景继续使用精确模式
4. 对边界数值和全量性能用例执行独立构建、精度与冷缓存复测

## 6. LLM 前置问题

- 目标实现是否满足：热点路径包含高占比逐元素除法，且当前使用高代价精确模式？
- 目标实现是否满足：算子验收允许有界相对或绝对误差，并能用全量数据验证误差？
- 目标实现是否满足：目标平台存在吞吐更高的 intrinsic 除法模式？
- 是否命中排除条件：要求逐位一致、严格 IEEE 舍入、0-ULP 或次正规数保真时不得降低精度模式？

## 7. 验收标准

正确性：

- 按每个 dtype 的正式 MRE/MARE 或 ULP 阈值覆盖零、极小值、极大值、Inf、NaN 与符号组合

性能：

- 区分计算受限和带宽受限形状，确认收益来自 Div 吞吐且非目标路径无回归

回滚信号：

- 特殊值语义改变、误差越界、目标平台模式不支持或计算受限形状没有稳定收益时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- ksearch-foreach-addcdiv-scalar-<run-id>（status=accepted, case=1, speedup=5.06）

## 检索卡（短卡）

动作：将向量Div从精确0-ULP配置切换为契约允许的硬件intrinsic快速模式。
适用：逐元素除法占热点、当前为高代价精确模式，且验收允许有界误差。
限制：仅用平台明确支持且满足精度阈值的模式；验证零、次正规数并保留必要语义。
范围：elementwise-arithmetic逐元素复合算术路径。
检索词：向量Div、0-ULP、intrinsic快速模式、FTZ、误差契约。
机会：热点逐元素除法仍使用0-ULP精确模式。
代价：极端输入误差、FTZ或特殊值行为可能不同于精确模式。
