---
type: Optimization
title: 散射乘归约的 GM CAS 原子更新
description: 用 GM CAS-loop 实现 Scatter multiply 的同址原子更新，替代标量 remap。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.atomic
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/gm-cas-atomic-multiply.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "anti_pattern_reasoning": {
    "dk-split-scalar-address-remap": "profile 与路径代码显示 multiply 的 D/K-split 同样会触发逐元素标量 remap 灾难。"
  },
  "applicability": {
    "constraints": [
      "目标 dtype 必须存在等宽 GM CAS，且 CAS-loop 需要在失败后基于最新 old 值重新计算乘积"
    ],
    "excluded_conditions": [
      "fp16、bf16、缺少等宽 CAS 的类型或高冲突下 CAS 重试成本超过原路径时不适用"
    ],
    "required_conditions": [
      "Scatter reduce 模式为 multiply，dtype 为 fp32、int32 或 int64，并存在同址并发更新"
    ]
  },
  "applicability_boundary": "仅适用于平台支持等宽 GM CAS 的 dtype；缺少等宽 CAS 的低精度类型必须回落到其他归约路径。",
  "classification": "validated_strategy",
  "classification_reason": "该机制依赖 scatter 重复索引、multiply-reduce 语义和可用 CAS 的 GM 数据类型，当前证据仅覆盖 scatter-update 类。",
  "confidence": "high",
  "created": "2026-08-21",
  "duplicate": {
    "existing_strategy_ids": [
      "S2"
    ],
    "reason": "与 GM 原子 scatter 种子共享直接定位更新原理，但乘法必须使用 CAS loop 并具有不同 dtype 边界。",
    "relation": "variant"
  },
  "evidence": [
    {
      "after_us": 2220.0,
      "before_us": 164825.787,
      "case": "5",
      "env": {
        "device": "0",
        "op_name": "Scatter",
        "post_eval_score": 75.33,
        "pre_eval_score": 71.5,
        "score_delta": "+3.83 (71.50→75.33)"
      },
      "operator_class": "scatter-update",
      "precision": "全 20 例过",
      "speedup": 74.0,
      "task_dir": "task_scatter_20260821_180115_5c6355f3"
    }
  ],
  "evidence_strength": "case5: 164825us→2220us (74x), 20/20 精度",
  "feature_signature": {
    "bottleneck": [
      "dk-split",
      "scalar-remap"
    ],
    "dtypes": [
      "fp32",
      "int32",
      "int64"
    ],
    "pattern": "scatter-write-mul-reduce",
    "reduce_mode": "mul",
    "structure": [
      "scatter",
      "indexed-write",
      "atomic-cas",
      "gm-atomic"
    ]
  },
  "gain": "74x",
  "generality": "op_class",
  "id": "S2-GmMulCAS",
  "implementation_steps": [
    "host 仅对 multiply 且平台能力表确认支持等宽 GM CAS 的 dtype 选择原子更新路径",
    "每个更新读取目标旧值，计算 new=old×update，并用 asc_atomic_cas 尝试提交",
    "CAS 失败时读取返回的最新值并重算，直到本次乘法成功串行化"
  ],
  "instance_ids": [],
  "intent": "消除散射乘归约分段路径中的标量地址重映射和逐更新 GM read-modify-write；在没有原子乘指令时用等宽 CAS 串行化同址更新。",
  "mechanism": "每个更新先读取目标旧值，计算 `new = old * update`，再用等宽 `asc_atomic_cas` 尝试提交；失败时用返回的最新值重新计算，直到成功。host 只对平台支持等宽 GM CAS 的 dtype 路由到该路径。",
  "name": "散射乘归约的 GM CAS 原子更新",
  "needs_human_review": false,
  "op": "scatter",
  "operator_class": "scatter-update",
  "operator_scope": "存在重复索引、归约模式为乘法且目标 dtype 支持等宽 GM CAS 的 scatter-update 数据流",
  "principle": "硬件没有直接原子乘时，可用 compare-and-swap 循环把同一 GM 地址上的 read-modify-write 串行化，使更新直接落到目标元素并绕过 D/K-split 标量 remap。",
  "provenance": {
    "final_summary": "opt/final_summary.json",
    "opt_md": "scatter_opt.md",
    "state_md": "STATE.md",
    "task_dir": "task_scatter_20260821_180115_5c6355f3"
  },
  "related_anti_patterns": [
    "dk-split-scalar-address-remap"
  ],
  "related_seed_ids": [
    "S2"
  ],
  "review_reason": "",
  "risks": [
    "索引高度冲突时 CAS 会频繁重试；浮点乘法顺序变化还可能改变舍入误差分布"
  ],
  "schema_version": 2,
  "slug": "gm-cas-atomic-multiply",
  "source": "task_dir",
  "status": "applied",
  "summary": "用 GM CAS-loop 实现 Scatter multiply 的同址原子更新，替代标量 remap。",
  "verification": {
    "correctness": [
      "覆盖重复索引、正负数、零值及 fp32/int32/int64，并验证 CAS 重试后的最终乘积"
    ],
    "performance": [
      "分别测量低冲突与高冲突索引分布，确认 CAS 重试开销没有抵消直接定位更新的收益"
    ],
    "rollback_signals": [
      "出现 CAS 不收敛、浮点误差超阈值、高冲突严重回归或不支持 dtype 误命中时回退"
    ]
  },
  "verified_by": "task_scatter_20260821_180115_5c6355f3"
}
-->

# 性能优化策略：散射乘归约的 GM CAS 原子更新

单一优化点：用 GM CAS-loop 实现 Scatter multiply 的同址原子更新，替代标量 remap。

## 1. 原理

硬件没有直接原子乘时，可用 compare-and-swap 循环把同一 GM 地址上的 read-modify-write 串行化，使更新直接落到目标元素并绕过 D/K-split 标量 remap。

实现机制：每个更新先读取目标旧值，计算 `new = old * update`，再用等宽 `asc_atomic_cas` 尝试提交；失败时用返回的最新值重新计算，直到成功。host 只对平台支持等宽 GM CAS 的 dtype 路由到该路径。

## 2. 性能问题模式

- 优化目标：消除散射乘归约分段路径中的标量地址重映射和逐更新 GM read-modify-write；在没有原子乘指令时用等宽 CAS 串行化同址更新。
- 适用数据流：存在重复索引、归约模式为乘法且目标 dtype 支持等宽 GM CAS 的 scatter-update 数据流
- Feature signature：`{"bottleneck": ["dk-split", "scalar-remap"], "dtypes": ["fp32", "int32", "int64"], "pattern": "scatter-write-mul-reduce", "reduce_mode": "mul", "structure": ["scatter", "indexed-write", "atomic-cas", "gm-atomic"]}`

## 3. 正确性红线

- 索引高度冲突时 CAS 会频繁重试；浮点乘法顺序变化还可能改变舍入误差分布

资源与硬件约束：

- 目标 dtype 必须存在等宽 GM CAS，且 CAS-loop 需要在失败后基于最新 old 值重新计算乘积

## 4. 泛化条件

- 策略作用域：op_class：scatter-update

适用：

- Scatter reduce 模式为 multiply，dtype 为 fp32、int32 或 int64，并存在同址并发更新

不适用：

- fp16、bf16、缺少等宽 CAS 的类型或高冲突下 CAS 重试成本超过原路径时不适用

## 5. 实施步骤

1. host 仅对 multiply 且平台能力表确认支持等宽 GM CAS 的 dtype 选择原子更新路径
2. 每个更新读取目标旧值，计算 new=old×update，并用 asc_atomic_cas 尝试提交
3. CAS 失败时读取返回的最新值并重算，直到本次乘法成功串行化

## 6. LLM 前置问题

- 目标实现是否满足：Scatter reduce 模式为 multiply，dtype 为 fp32、int32 或 int64，并存在同址并发更新？
- 是否命中排除条件：fp16、bf16、缺少等宽 CAS 的类型或高冲突下 CAS 重试成本超过原路径时不适用？

## 7. 验收标准

正确性：

- 覆盖重复索引、正负数、零值及 fp32/int32/int64，并验证 CAS 重试后的最终乘积

性能：

- 分别测量低冲突与高冲突索引分布，确认 CAS 重试开销没有抵消直接定位更新的收益

回滚信号：

- 出现 CAS 不收敛、浮点误差超阈值、高冲突严重回归或不支持 dtype 误命中时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：dk-split-scalar-address-remap

- task_scatter_20260821_180115_5c6355f3（case=5, speedup=74.0）

## 检索卡（短卡）

动作：将逐更新 GM read-modify-write 改为等宽 CAS 循环：读取旧值、计算 old×update 后尝试提交。
适用：scatter reduce 为 multiply，dtype 为 fp32、int32 或 int64，且存在同址并发更新。
限制：仅在平台支持对应 dtype 的等宽 GM CAS 时启用；排除 fp16、bf16 及缺少等宽 CAS。
范围：scatter-reduce 的 multiply 同址更新路径。
检索词：GM CAS、compare-and-swap、scatter multiply、D/K-split、read-modify-write。
机会：存在重复索引与同址更新，且无原子乘指令，路径仍做标量 remap 和逐更新 GM RMW。
代价：高冲突索引会频繁重试；浮点乘法顺序变化可能改变舍入误差分布。
