---
type: Optimization
title: 可证明恒等行映射的整行缓存与向量索引读取
description: 解析证明 Gather 行映射恒等后启用整行 UB 加载与 SIMD Gather 快路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/row-map-identity-analytic.md
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
      "host tiling 必须能证明输出行到输入行的映射恒等，不能仅凭维度相等进行推断"
    ],
    "excluded_conditions": [
      "输出行与输入行存在间隔、广播、置换或非恒等步幅时禁止启用"
    ],
    "required_conditions": [
      "索引轴为末轴，且各维 shape/stride 能证明输出行到输入行的基址映射恒等"
    ]
  },
  "applicability_boundary": "索引轴为末轴且行映射可解析证明恒等；存在间隔、广播、置换或非恒等步幅时不适用",
  "classification": "validated_strategy",
  "classification_reason": "该机制依赖 gather 索引读数据流与可证明的恒等行映射，当前证据仅覆盖 index-gather 算子类。",
  "confidence": "high",
  "created": "2026-08-22",
  "duplicate": {
    "existing_strategy_ids": [],
    "reason": "现有 registry 中没有同时覆盖恒等行映射解析和索引读快路径边界的策略。",
    "relation": "new"
  },
  "evidence": [
    {
      "after_us": 5.808,
      "before_us": 183.586,
      "case": "7",
      "env": {
        "op_name": "Gather",
        "post_eval_score": 72.90900199945968,
        "pre_eval_score": 70.8702166585414,
        "score_delta": "+2.04"
      },
      "operator_class": "index-gather",
      "speedup": 31.609,
      "task_dir": "task_gather_20260821_233432_43a4c0"
    },
    {
      "after_us": 5.429,
      "before_us": 183.7,
      "case": "7",
      "note": "same mechanism as task_gather_20260821_233432_43a4c0 (31.609x accepted); re-verified 33.84x but rejected on sample-stability gate: attempt2 relative_mad=0.0658/cv=0.092 > 0.02/0.03, baseline global stable=false -> comparison.ok=false, accept impossible",
      "operator_class": "index-gather",
      "precision": "case 7 verify ok=true, MISMATCH=0",
      "round": 1,
      "run_id": "<run-id>",
      "speedup": 33.84,
      "status": "rejected"
    },
    {
      "comparison_sha256": "ae0cd9fe39b4e4d2834d4957bbb6824ebaf6b32dad4bff591588766aec8fd2b7",
      "decision_sha256": "79d8c74e32869b081933e144435498239de2b5496101b3cea756fe7436bba907",
      "operator_class": "index-gather",
      "performance_sha256": "c82b95c01d3cc5cbc7d54952e1ff8f8a72e7c3c8a5927a2d085828fa7b0e5f1d",
      "round": 1,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "3762830c2c56044868f48201758b6f5c29e21f87b20dfaf5846d697df17f87f9",
      "verify_sha256": "50643dc398c644773725c5455b04462b2cd6a1b9416124aaccfcedea3d197a93"
    },
    {
      "case": "case 7（T1 标量回退例，rowMapIdentity 可解析恒等但 host 未解析）",
      "note": "同机制第二 run 独立复现；本 run 以解析判据替代数据依赖判定，incremental 1.0243",
      "operator_class": "index-gather",
      "precision": "20/20 PASS",
      "round": 1,
      "run_id": "<run-id>",
      "speedup": "30.92x（183.9→5.95us/inv；SIMD 路由翻转直接证据 aiv_vec_time 0→8.03us）",
      "status": "accepted"
    },
    {
      "comparison_sha256": "56ad35a422326388fa9ff0b94d35f4462c89e41340c71abb6cdcf99d78cb48e4",
      "decision_sha256": "fde820019f7aa8859f2add9add6a50fdc1186f61e6fc8e180ff04b4c637f40ee",
      "operator_class": "index-gather",
      "performance_sha256": "7619835e823cc61326efa2a1f1072cd7f0f69be1f0348d6291c203ce6d4b01ee",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "ee3046dab4ab25337f02076e29d91a18a19b91d30a36f07d466a8c341b141ce2",
      "verify_sha256": "01077c31b94adc7fc18cf41720cfee9fa3b88445e9c257f0c94becc2b9d49126"
    }
  ],
  "evidence_strength": "case_7 31.609x，全 20 case verify 过，无回归",
  "feature_signature": {
    "bottleneck": [
      "scalar-gm-read"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32",
      "int8",
      "int32",
      "int64"
    ],
    "pattern": "row-map-identity-analytic",
    "reduce_mode": "indexed-read",
    "structure": [
      "indexed-read",
      "simd-gather",
      "row-mapping"
    ]
  },
  "gain": "case_7: 183.586us→5.808us (31.6x)",
  "generality": "op_class",
  "id": "G1-RowMapIdentityAnalytic",
  "implementation_steps": [
    "在 host tiling 中用各维 stride 与 index 前缀乘积计算行映射是否恒等",
    "仅在恒等判定成立时设置对应 tiling 能力标记，并选择整行 UB 加载与 SIMD Gather 路径",
    "保留原标量 GM 读取路径作为非恒等映射的正确性回退"
  ],
  "instance_ids": [],
  "intent": "消除可缓存整行被保守路由到逐元素 GM 随机读取所产生的访存与标量控制开销。",
  "mechanism": "host 根据规范化后的 shape 与 stride 逐维验证源行基址是否只由输出前缀行决定，且索引轴不额外改变行基址；证明成立后，将候选输入行连续搬入 UB，在片上使用向量 Gather 完成行内索引读取，否则保持逐元素 GM 回退。",
  "name": "可证明恒等行映射的整行缓存与向量索引读取",
  "needs_human_review": false,
  "op": "gather",
  "operator_class": "index-gather",
  "operator_scope": "索引轴为末轴、输出行到输入行的基址映射可解析证明恒等的 indexed-read 数据流",
  "principle": "当输出行与输入行存在可证明的一一恒等映射时，索引只改变行内选择而不改变行基址，可将输入整行搬入 UB 后使用 SIMD Gather，避免每个元素独立访问 GM。",
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
    "恒等条件判定过宽会在 gap、广播或跨行索引场景读取错误行，属于静默精度风险"
  ],
  "schema_version": 2,
  "slug": "row-map-identity-analytic",
  "source": "task_dir",
  "status": "applied",
  "summary": "解析证明 Gather 行映射恒等后启用整行 UB 加载与 SIMD Gather 快路径。",
  "verification": {
    "correctness": [
      "覆盖恒等与非恒等行映射、不同 index dtype，并确认全量精度用例通过"
    ],
    "performance": [
      "分别比较命中快路径和回退路径的多组 shape 中位耗时，确认非目标路径无回归"
    ],
    "rollback_signals": [
      "任一非恒等 shape 误命中整行缓存路径、出现跨行错误或全量性能回归时立即回退"
    ]
  },
  "verified_by": "task_gather_20260821_233432_43a4c0"
}
-->

# 性能优化策略：可证明恒等行映射的整行缓存与向量索引读取

单一优化点：解析证明 Gather 行映射恒等后启用整行 UB 加载与 SIMD Gather 快路径。

## 1. 原理

当输出行与输入行存在可证明的一一恒等映射时，索引只改变行内选择而不改变行基址，可将输入整行搬入 UB 后使用 SIMD Gather，避免每个元素独立访问 GM。

实现机制：host 根据规范化后的 shape 与 stride 逐维验证源行基址是否只由输出前缀行决定，且索引轴不额外改变行基址；证明成立后，将候选输入行连续搬入 UB，在片上使用向量 Gather 完成行内索引读取，否则保持逐元素 GM 回退。

## 2. 性能问题模式

- 优化目标：消除可缓存整行被保守路由到逐元素 GM 随机读取所产生的访存与标量控制开销。
- 适用数据流：索引轴为末轴、输出行到输入行的基址映射可解析证明恒等的 indexed-read 数据流
- Feature signature：`{"bottleneck": ["scalar-gm-read"], "dtypes": ["fp16", "bf16", "fp32", "int8", "int32", "int64"], "pattern": "row-map-identity-analytic", "reduce_mode": "indexed-read", "structure": ["indexed-read", "simd-gather", "row-mapping"]}`

## 3. 正确性红线

- 恒等条件判定过宽会在 gap、广播或跨行索引场景读取错误行，属于静默精度风险

资源与硬件约束：

- host tiling 必须能证明输出行到输入行的映射恒等，不能仅凭维度相等进行推断

## 4. 泛化条件

- 策略作用域：op_class：index-gather

适用：

- 索引轴为末轴，且各维 shape/stride 能证明输出行到输入行的基址映射恒等

不适用：

- 输出行与输入行存在间隔、广播、置换或非恒等步幅时禁止启用

## 5. 实施步骤

1. 在 host tiling 中用各维 stride 与 index 前缀乘积计算行映射是否恒等
2. 仅在恒等判定成立时设置对应 tiling 能力标记，并选择整行 UB 加载与 SIMD Gather 路径
3. 保留原标量 GM 读取路径作为非恒等映射的正确性回退

## 6. LLM 前置问题

- 目标实现是否满足：索引轴为末轴，且各维 shape/stride 能证明输出行到输入行的基址映射恒等？
- 是否命中排除条件：输出行与输入行存在间隔、广播、置换或非恒等步幅时禁止启用？

## 7. 验收标准

正确性：

- 覆盖恒等与非恒等行映射、不同 index dtype，并确认全量精度用例通过

性能：

- 分别比较命中快路径和回退路径的多组 shape 中位耗时，确认非目标路径无回归

回滚信号：

- 任一非恒等 shape 误命中整行缓存路径、出现跨行错误或全量性能回归时立即回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- task_gather_20260821_233432_43a4c0（case=7, speedup=31.609）
- gather-20260823_213117-f09ddc（round=1, status=rejected, case=7, speedup=33.84）
- gather-20260823_213117-f09ddc（round=1, status=rejected）
- gather-20260831_113139-a1e0e0（round=1, status=accepted, case=case 7（T1 标量回退例，rowMapIdentity 可解析恒等但 host 未解析）, speedup=30.92x（183.9→5.95us/inv；SIMD 路由翻转直接证据 aiv_vec_time 0→8.03us））
- gather-20260831_113139-a1e0e0（round=1, status=accepted）

## 检索卡（短卡）

动作：仅在host证明行映射恒等时，将逐元素GM随机读取改为整行载入UB后用SIMD Gather取数。
适用：索引轴为末轴，shape与stride可证明输出行到输入行的基址映射恒等。
限制：host tiling必须严格证明恒等映射；gap、广播或跨行索引不得误判。
范围：index-gather的末轴indexed-read路径。
检索词：行映射恒等、shape/stride、整行UB加载、SIMD Gather、tiling标记。
机会：可缓存整行仍被保守路由为逐元素GM随机读取。
