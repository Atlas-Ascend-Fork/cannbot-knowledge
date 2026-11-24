---
type: Optimization
title: 按数据足迹自适应扩大离散索引读取分块
description: 按 dtype、线程临时量和 UB 预算自适应扩大离散索引读取的 chunk，减少分块循环次数。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/t2-narrow-dtype-ub-chunk-raise.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "anti_pattern_reasoning": {},
  "applicability": {
    "constraints": [
      "chunk 对应的 SIMT 线程数不得超过目标平台上限，且总 UB 与单线程足迹必须通过统一安全校验"
    ],
    "excluded_conditions": [
      "int32+int32、int64 或其他单线程足迹较大的组合不得无条件放大 chunk"
    ],
    "required_conditions": [
      "离散索引读取无法整行缓存，且输入与索引 dtype 组合具有足够小的单线程存储足迹"
    ]
  },
  "applicability_boundary": "非末轴离散索引读取且 dtype 组合的单线程足迹较小；宽 dtype 或 UB 余量不足时不扩大分块",
  "classification": "validated_strategy",
  "classification_reason": "该机制依赖 gather 离散索引读与窄 dtype 下的 UB 容量余量，当前证据仅覆盖 index-gather 算子类。",
  "confidence": "high",
  "created": "2026-08-22",
  "duplicate": {
    "existing_strategy_ids": [],
    "reason": "现有 registry 中没有兼具窄 dtype UB 分块扩容和离散 gather 读批处理边界的策略。",
    "relation": "new"
  },
  "evidence": [
    {
      "after_us": 4479.826,
      "before_us": 4924.314,
      "case": "6",
      "env": {
        "op_name": "Gather",
        "post_eval_score": 72.90900199945968,
        "pre_eval_score": 70.8702166585414,
        "score_delta": "+2.04"
      },
      "operator_class": "index-gather",
      "speedup": 1.099,
      "task_dir": "task_gather_20260821_233432_43a4c0"
    },
    {
      "before_us": 5.152,
      "case": "13",
      "env": {
        "op_name": "Gather",
        "post_eval_score": 72.90900199945968,
        "pre_eval_score": 70.8702166585414,
        "score_delta": "+2.04"
      },
      "operator_class": "index-gather",
      "speedup": 0.914,
      "task_dir": "task_gather_20260821_233432_43a4c0"
    }
  ],
  "evidence_strength": "case_6 1.099x，其余 case 无回归（case_13 0.914x 为 T1 路径噪声）",
  "feature_signature": {
    "bottleneck": [
      "scattered-gm-read",
      "mte-descriptor-spray"
    ],
    "dtypes": [
      "int8",
      "fp16",
      "bf16",
      "int32"
    ],
    "pattern": "scatter-read-chunk-amortize",
    "reduce_mode": "indexed-read",
    "structure": [
      "indexed-read",
      "simt-scatter",
      "chunk-batching"
    ]
  },
  "gain": "case_6: 4924.314us→4479.826us (1.099x)",
  "generality": "op_class",
  "id": "G2-T2UbChunkRaise",
  "implementation_steps": [
    "按输入 dtype、索引 dtype 和 UB 预算计算允许的 chunk 上限",
    "在平台最大线程数、单次指令字段上限和 UB 容量约束内选择尽可能大的安全 chunk",
    "在 host 与 kernel 两侧执行同一足迹和容量校验，不满足时保持保守分块"
  ],
  "instance_ids": [],
  "intent": "利用窄 dtype 的较小单线程足迹扩大离散索引读取分块，提高每轮并发度并减少外层 chunk 迭代。",
  "mechanism": "host 按数据 dtype、索引 dtype、每线程临时量、UB 可用容量和 SIMT 最大线程数共同求解 chunk 上限；kernel 以该上限增加单次 grid-stride 迭代覆盖的更新数，减少外层 chunk 循环，同时保留足迹与容量校验作为安全网。",
  "name": "按数据足迹自适应扩大离散索引读取分块",
  "needs_human_review": false,
  "op": "gather",
  "operator_class": "index-gather",
  "operator_scope": "非末轴离散索引读取、每线程数据和索引足迹较小且外层分块循环占比明显的路径",
  "principle": "离散读取路径的外层循环次数与 chunk 大小近似成反比；窄 dtype 的每线程索引、数据和临时量足迹较小，在不突破平台线程上限与 UB 容量时扩大 chunk，可以摊销循环控制、同步与指令发射开销。",
  "provenance": {
    "final_summary": "opt/final_summary.json",
    "opt_md": "",
    "state_md": "STATE.md",
    "task_dir": "task_gather_20260821_233432_43a4c0"
  },
  "related_anti_patterns": [],
  "related_seed_ids": [],
  "review_reason": "",
  "risks": [
    "忽略 dtype 足迹直接统一放大 chunk 可能造成 UB 超限、编译失败或设备运行异常"
  ],
  "schema_version": 2,
  "slug": "t2-narrow-dtype-ub-chunk-raise",
  "source": "task_dir",
  "status": "applied",
  "summary": "按 dtype、线程临时量和 UB 预算自适应扩大离散索引读取的 chunk，减少分块循环次数。",
  "verification": {
    "correctness": [
      "覆盖窄 dtype 命中路径和宽 dtype 回退路径，并执行全部 Gather 精度用例"
    ],
    "performance": [
      "比较大规模离散读取的分块数与中位耗时，同时检查末轴路径和宽 dtype 路径无回归"
    ],
    "rollback_signals": [
      "出现 UB 超限、设备异常、宽 dtype 误命中或代表性 shape 收益低于测量噪声时回退"
    ]
  },
  "verified_by": "task_gather_20260821_233432_43a4c0"
}
-->

# 性能优化策略：按数据足迹自适应扩大离散索引读取分块

单一优化点：按 dtype、线程临时量和 UB 预算自适应扩大离散索引读取的 chunk，减少分块循环次数。

## 1. 原理

离散读取路径的外层循环次数与 chunk 大小近似成反比；窄 dtype 的每线程索引、数据和临时量足迹较小，在不突破平台线程上限与 UB 容量时扩大 chunk，可以摊销循环控制、同步与指令发射开销。

实现机制：host 按数据 dtype、索引 dtype、每线程临时量、UB 可用容量和 SIMT 最大线程数共同求解 chunk 上限；kernel 以该上限增加单次 grid-stride 迭代覆盖的更新数，减少外层 chunk 循环，同时保留足迹与容量校验作为安全网。

## 2. 性能问题模式

- 优化目标：利用窄 dtype 的较小单线程足迹扩大离散索引读取分块，提高每轮并发度并减少外层 chunk 迭代。
- 适用数据流：非末轴离散索引读取、每线程数据和索引足迹较小且外层分块循环占比明显的路径
- Feature signature：`{"bottleneck": ["scattered-gm-read", "mte-descriptor-spray"], "dtypes": ["int8", "fp16", "bf16", "int32"], "pattern": "scatter-read-chunk-amortize", "reduce_mode": "indexed-read", "structure": ["indexed-read", "simt-scatter", "chunk-batching"]}`

## 3. 正确性红线

- 忽略 dtype 足迹直接统一放大 chunk 可能造成 UB 超限、编译失败或设备运行异常

资源与硬件约束：

- chunk 对应的 SIMT 线程数不得超过目标平台上限，且总 UB 与单线程足迹必须通过统一安全校验

## 4. 泛化条件

- 策略作用域：op_class：index-gather

适用：

- 离散索引读取无法整行缓存，且输入与索引 dtype 组合具有足够小的单线程存储足迹

不适用：

- int32+int32、int64 或其他单线程足迹较大的组合不得无条件放大 chunk

## 5. 实施步骤

1. 按输入 dtype、索引 dtype 和 UB 预算计算允许的 chunk 上限
2. 在平台最大线程数、单次指令字段上限和 UB 容量约束内选择尽可能大的安全 chunk
3. 在 host 与 kernel 两侧执行同一足迹和容量校验，不满足时保持保守分块

## 6. LLM 前置问题

- 目标实现是否满足：离散索引读取无法整行缓存，且输入与索引 dtype 组合具有足够小的单线程存储足迹？
- 是否命中排除条件：int32+int32、int64 或其他单线程足迹较大的组合不得无条件放大 chunk？

## 7. 验收标准

正确性：

- 覆盖窄 dtype 命中路径和宽 dtype 回退路径，并执行全部 Gather 精度用例

性能：

- 比较大规模离散读取的分块数与中位耗时，同时检查末轴路径和宽 dtype 路径无回归

回滚信号：

- 出现 UB 超限、设备异常、宽 dtype 误命中或代表性 shape 收益低于测量噪声时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- task_gather_20260821_233432_43a4c0（case=6, speedup=1.099）
- task_gather_20260821_233432_43a4c0（case=13, speedup=0.914）

## 检索卡（短卡）

动作：按输入及索引 dtype 的数据足迹和 UB 预算，自适应扩大离散读取 chunk。
适用：离散索引读取无法整行缓存，且输入与索引 dtype 的单线程足迹足够小。
限制：chunk 不得超过平台线程数、单次指令字段及 UB 容量上限。
范围：index-gather 的非末轴离散索引读取路径。
检索词：非末轴离散索引读取、窄 dtype、chunk、SIMT 线程数、UB 预算。
机会：窄 dtype 单线程足迹较小，而小 chunk 导致较多外层循环。
代价：忽略 dtype 足迹统一放大会导致 UB 超限、编译失败或设备异常。
