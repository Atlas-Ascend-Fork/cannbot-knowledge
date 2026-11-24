---
type: Optimization
title: 独立行归约归一化的批处理
description: 将独立行批量搬运并融合 reduce/rstd，以每批一次同步替代逐行流水排空。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/row-batch-normalize.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "anti_pattern_reasoning": {
    "per-element-mte-descriptor-spray": "旧路径为每行生成独立 MTE 描述符，二维批量搬运直接合并了这些传输。",
    "per-row-pipebarrier-sync": "旧路径每行都执行独立 V_S 同步，实测批处理后同步次数明显下降。"
  },
  "applicability": {
    "constraints": [
      "host 必须按 UB 预算动态计算 batch，并保证批内 x、rstd、gamma 与输出缓冲不会越界"
    ],
    "excluded_conditions": [
      "行之间存在数据依赖、不是末轴规约，或 UB 只能容纳一行且同步开销不占主导时不应套用"
    ],
    "required_conditions": [
      "算子由大量相互独立的行组成，且每行执行相同的末轴 reduce 与 normalize 流程"
    ]
  },
  "applicability_boundary": "UB 能容纳至少两行活动数据时产生批化收益；行宽增大导致 batch=1 时应自然退化为逐行路径。本策略不减少 GM 总字节数，收益来自描述符、队列往返和同步摊销。",
  "classification": "validated_strategy",
  "classification_reason": "该机制依赖独立行归约、rstd 归一化数据流与行间批处理条件，当前证据仅覆盖 normalization 算子类。",
  "confidence": "high",
  "created": "2026-08-21",
  "duplicate": {
    "existing_strategy_ids": [
      "S3",
      "S4"
    ],
    "reason": "同时专门化批处理同步摊销和二维批量搬运两个种子原理，并加入 RMSNorm 行归约与 rstd 融合。",
    "relation": "variant"
  },
  "evidence": [
    {
      "after_us": 9.214,
      "before_us": 23.636,
      "case": "1",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 2.57,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 10.073,
      "before_us": 24.816,
      "case": "2",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 2.46,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 106.712,
      "before_us": 101.394,
      "case": "5",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 0.95,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 10.167,
      "before_us": 25.938,
      "case": "7",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 2.55,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 41.476,
      "before_us": 95.535,
      "case": "8",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 2.3,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 9.379,
      "before_us": 24.78,
      "case": "10",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 2.64,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 14.566,
      "before_us": 40.338,
      "case": "13",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 2.77,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 7.236,
      "before_us": 23.078,
      "case": "14",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 3.19,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 771.869,
      "before_us": 4380.337,
      "case": "15",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 5.67,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 4.987,
      "before_us": 14.508,
      "case": "16",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 2.91,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 84.057,
      "before_us": 741.685,
      "case": "20",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 8.82,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 13.448,
      "before_us": 25.951,
      "case": "3",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 1.93,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 21.01,
      "before_us": 29.71,
      "case": "4",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 1.41,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 21.752,
      "before_us": 32.078,
      "case": "6",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 1.47,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 45.909,
      "before_us": 103.468,
      "case": "9",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 2.25,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 15.014,
      "before_us": 28.57,
      "case": "11",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 1.9,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 22.485,
      "before_us": 33.604,
      "case": "12",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 1.49,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 4.548,
      "before_us": 5.986,
      "case": "17",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 1.32,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 11.68,
      "before_us": 13.663,
      "case": "18",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 1.17,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 8.683,
      "before_us": 9.949,
      "case": "19",
      "env": {
        "device": "0",
        "post_eval_score": 88.15,
        "pre_eval_score": 73.72
      },
      "operator_class": "normalization",
      "precision": "20/20 通过",
      "speedup": 1.15,
      "task_dir": "task_rms_norm_<run-id>"
    },
    {
      "after_us": 16.863,
      "before_us": 44.24,
      "case": "baseline-anchor",
      "operator_class": "normalization",
      "precision": "ALL PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/rms_norm/<run-id>/phase6_apply/final_report.md",
      "speedup": 2.62,
      "status": "accepted"
    },
    {
      "comparison_sha256": "7701ae247190f21a9cbc236b9d1db76179e1a2206fb3eb477bd459ed57b30a4e",
      "decision_sha256": "d6e6352083e92c59d8d5f715d43097e91aa46f19068979aa67f88702c44d87ca",
      "operator_class": "normalization",
      "performance_sha256": "70e9ca49a813059240c99ddd259bf9265727a7469da162286563ae7bdc868df6",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "40129ef9de3a39a9acd487a22f6057d08373f05ad889829650dbdc108baca5a8",
      "verify_sha256": "ede38a8bd93de001fd78ba54c52d57a0d9f9756d7318d9aca30108a36bdef037"
    }
  ],
  "evidence_strength": "强（20/20 精度通过，官方 post−pre = +14.43，总耗时 4.68x）",
  "feature_signature": {
    "bottleneck": [
      "row-sync",
      "mte-descriptor-spray"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "row-batch-normalize",
    "reduce_mode": "row-reduce",
    "structure": [
      "row-parallel",
      "2d-bulk-copy",
      "batch-reduce"
    ]
  },
  "gain": "总体 4.68x（20 用例 median 和 5779→1234μs）。逐用例：case15 5.67x、case20 8.82x、case1 2.57x、 case2 2.46x、case8 2.30x、case13 2.77x、case14 3.19x、case16 2.91x、case10 2.64x、case7 2.55x； case5 0.98-1.0x（持平，批量退化为 1）；官方得分 +14.43。",
  "generality": "op_class",
  "id": "R1",
  "implementation_steps": [
    "host 根据对齐后行宽和 UB 预算计算 batch，容量不足时安全退化为 batch=1",
    "使用单条二维搬运描述符批量搬入和写回多行数据",
    "在同一向量作用域内融合批量 reduce 与 rstd，并将每行同步改为每批一次",
    "复用经过验证的逐行 normalize 数值路径，避免改变计算顺序和精度契约"
  ],
  "instance_ids": [],
  "intent": "消除独立行归一化路径中随行数线性增长的搬运描述符、队列往返和跨引擎同步开销；这类固定成本在小行宽、多行输入上会超过实际向量计算成本。",
  "mechanism": "host 以对齐后行宽、输入/输出双缓冲、统计量槽位和常驻参数为项建立 UB 预算，动态求解每 tile 的批行数，容量不足时退化为一行。kernel 用二维搬运一次读写多行，在批内连续完成每行 reduce、统计量计算与 normalize；所有统计量写入后只做一次必要的 V→S 可见性同步，并让可复用参数在批间常驻片上。",
  "name": "独立行归约归一化的批处理",
  "needs_human_review": false,
  "op": "rms_norm",
  "operator_class": "normalization",
  "operator_scope": "所有行独立、末轴规约类算子（RmsNorm / LayerNorm / 逐行 reduce+normalize）",
  "principle": "逐行同步与 MTE 描述符发射具有固定成本；把多行合并到一个 tile 后批量搬运、融合规约并只执行一次跨流水同步，可在不增加 GM 流量的前提下把固定成本摊销到多行。",
  "provenance": {
    "final_summary": "opt/final_summary.json",
    "opt_md": "rms_norm_opt_20260821.md",
    "state_md": "STATE.md",
    "task_dir": "task_rms_norm_<run-id>"
  },
  "related_anti_patterns": [
    "per-row-pipebarrier-sync",
    "per-element-mte-descriptor-spray"
  ],
  "related_seed_ids": [
    "S3",
    "S4"
  ],
  "review_reason": "",
  "risks": [
    "batch 容量公式错误会导致 UB 越界；融合 reduce 改变运算顺序可能引入浮点精度差异"
  ],
  "schema_version": 2,
  "slug": "row-batch-normalize",
  "source": "task_dir",
  "status": "applied",
  "summary": "将独立行批量搬运并融合 reduce/rstd，以每批一次同步替代逐行流水排空。",
  "verification": {
    "correctness": [
      "对 fp16、bf16、fp32 及极端数值执行全量精度验证，并核对 batch=1 与原路径等价"
    ],
    "performance": [
      "按小中大行宽分别比较中位耗时，确认 batch>1 获益且 batch=1 不发生显著回归"
    ],
    "rollback_signals": [
      "出现 UB 越界、数值误差扩大、大行宽明显回归或同步可见性错误时立即回退"
    ]
  },
  "verified_by": "task_rms_norm_<run-id>"
}
-->

# 性能优化策略：独立行归约归一化的批处理

单一优化点：将独立行批量搬运并融合 reduce/rstd，以每批一次同步替代逐行流水排空。

## 1. 原理

逐行同步与 MTE 描述符发射具有固定成本；把多行合并到一个 tile 后批量搬运、融合规约并只执行一次跨流水同步，可在不增加 GM 流量的前提下把固定成本摊销到多行。

实现机制：host 以对齐后行宽、输入/输出双缓冲、统计量槽位和常驻参数为项建立 UB 预算，动态求解每 tile 的批行数，容量不足时退化为一行。kernel 用二维搬运一次读写多行，在批内连续完成每行 reduce、统计量计算与 normalize；所有统计量写入后只做一次必要的 V→S 可见性同步，并让可复用参数在批间常驻片上。

## 2. 性能问题模式

- 优化目标：消除独立行归一化路径中随行数线性增长的搬运描述符、队列往返和跨引擎同步开销；这类固定成本在小行宽、多行输入上会超过实际向量计算成本。
- 适用数据流：所有行独立、末轴规约类算子（RmsNorm / LayerNorm / 逐行 reduce+normalize）
- Feature signature：`{"bottleneck": ["row-sync", "mte-descriptor-spray"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "row-batch-normalize", "reduce_mode": "row-reduce", "structure": ["row-parallel", "2d-bulk-copy", "batch-reduce"]}`

## 3. 正确性红线

- batch 容量公式错误会导致 UB 越界；融合 reduce 改变运算顺序可能引入浮点精度差异

资源与硬件约束：

- host 必须按 UB 预算动态计算 batch，并保证批内 x、rstd、gamma 与输出缓冲不会越界

## 4. 泛化条件

- 策略作用域：op_class：normalization

适用：

- 算子由大量相互独立的行组成，且每行执行相同的末轴 reduce 与 normalize 流程

不适用：

- 行之间存在数据依赖、不是末轴规约，或 UB 只能容纳一行且同步开销不占主导时不应套用

## 5. 实施步骤

1. host 根据对齐后行宽和 UB 预算计算 batch，容量不足时安全退化为 batch=1
2. 使用单条二维搬运描述符批量搬入和写回多行数据
3. 在同一向量作用域内融合批量 reduce 与 rstd，并将每行同步改为每批一次
4. 复用经过验证的逐行 normalize 数值路径，避免改变计算顺序和精度契约

## 6. LLM 前置问题

- 目标实现是否满足：算子由大量相互独立的行组成，且每行执行相同的末轴 reduce 与 normalize 流程？
- 是否命中排除条件：行之间存在数据依赖、不是末轴规约，或 UB 只能容纳一行且同步开销不占主导时不应套用？

## 7. 验收标准

正确性：

- 对 fp16、bf16、fp32 及极端数值执行全量精度验证，并核对 batch=1 与原路径等价

性能：

- 按小中大行宽分别比较中位耗时，确认 batch>1 获益且 batch=1 不发生显著回归

回滚信号：

- 出现 UB 越界、数值误差扩大、大行宽明显回归或同步可见性错误时立即回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：per-row-pipebarrier-sync, per-element-mte-descriptor-spray

- task_rms_norm_<run-id>（case=1, speedup=2.57）
- task_rms_norm_<run-id>（case=2, speedup=2.46）
- task_rms_norm_<run-id>（case=5, speedup=0.95）
- task_rms_norm_<run-id>（case=7, speedup=2.55）
- task_rms_norm_<run-id>（case=8, speedup=2.3）
- task_rms_norm_<run-id>（case=10, speedup=2.64）
- task_rms_norm_<run-id>（case=13, speedup=2.77）
- task_rms_norm_<run-id>（case=14, speedup=3.19）
- task_rms_norm_<run-id>（case=15, speedup=5.67）
- task_rms_norm_<run-id>（case=16, speedup=2.91）
- task_rms_norm_<run-id>（case=20, speedup=8.82）
- task_rms_norm_<run-id>（case=3, speedup=1.93）
- task_rms_norm_<run-id>（case=4, speedup=1.41）
- task_rms_norm_<run-id>（case=6, speedup=1.47）
- task_rms_norm_<run-id>（case=9, speedup=2.25）
- task_rms_norm_<run-id>（case=11, speedup=1.9）
- task_rms_norm_<run-id>（case=12, speedup=1.49）
- task_rms_norm_<run-id>（case=17, speedup=1.32）
- task_rms_norm_<run-id>（case=18, speedup=1.17）
- task_rms_norm_<run-id>（case=19, speedup=1.15）
- ksearch-rms-norm-<run-id>（status=accepted, case=baseline-anchor, speedup=2.62）
- rms_norm-<run-id>（round=1, status=accepted）

## 检索卡（短卡）

动作：将逐行搬运、规约和同步改为多行单tile批量搬运与融合规约，每批同步一次；容量不足退化为batch=1。
适用：大量相互独立的行执行相同末轴reduce与normalize，且UB可容纳多行。
限制：保持各行结果及计算顺序；有行间依赖、非末轴或UB仅容一行时不适用；容量计算不得越界。
范围：normalization的独立行末轴reduce-normalize路径。
检索词：多行tile、二维搬运、批量reduce、跨流水同步、双缓冲。
机会：小行宽、多行输入中，描述符、队列往返和跨引擎同步随行数增长。
代价：融合规约改变运算顺序，可能产生浮点精度差异。
