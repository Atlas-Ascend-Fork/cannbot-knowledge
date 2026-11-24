---
type: Optimization
title: 低精度散射加的 FP32 工作区原子累加
description: 使用 FP32 GM 工作区完成 Scatter 低精度 add 原子累加，并在末尾一次舍回。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/gm-fp32-workspace-atomic-add.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "anti_pattern_reasoning": {
    "dk-split-scalar-address-remap": "profile 和旧路径代码均显示 D/K-split 后存在逐元素 GetValue/SetValue 标量 remap。",
    "simt-write-mte-read-visibility-gap": "实测确认缺少 threadfence 时后续 MTE 会读到陈旧工作区数据并丢失更新。"
  },
  "applicability": {
    "constraints": [
      "必须预留 numel×4B 的 fp32 workspace，并在 host tiling 与 GetWorkspaceSize 中使用相同判据"
    ],
    "excluded_conditions": [
      "非 add 归约、workspace 不足或无法提供 fp32 GM 原子加与写后可见性保证时禁止启用"
    ],
    "required_conditions": [
      "Scatter reduce 模式为 add，输出 dtype 为 fp16 或 bf16，且低精度直接累加不能满足精度要求"
    ]
  },
  "applicability_boundary": "fp16/bf16 add，workspace=numel×4B；host gmAddWs 路由 + GetWorkspaceSize 预留",
  "classification": "validated_strategy",
  "classification_reason": "该机制依赖 scatter 重复索引、add-reduce 语义和低精度输出，当前证据仅覆盖 scatter-update 算子类。",
  "confidence": "high",
  "created": "2026-08-21",
  "duplicate": {
    "existing_strategy_ids": [
      "S1"
    ],
    "reason": "共享工作区归约原理，但新增 FP32 GM 原子累加、低精度单次舍回和写后可见性约束。",
    "relation": "variant"
  },
  "evidence": [
    {
      "after_us": 1281.0,
      "before_us": 426502.496,
      "case": "4",
      "env": {
        "device": "0",
        "op_name": "Scatter",
        "post_eval_score": 75.33,
        "pre_eval_score": 71.5,
        "score_delta": "+3.83 (71.50→75.33)"
      },
      "operator_class": "scatter-update",
      "precision": "全 20 例过",
      "speedup": 333.0,
      "task_dir": "task_scatter_20260821_180115_5c6355f3"
    },
    {
      "after_us": 42.9,
      "before_us": 779.097,
      "case": "18",
      "env": {
        "device": "0",
        "op_name": "Scatter",
        "post_eval_score": 75.33,
        "pre_eval_score": 71.5,
        "score_delta": "+3.83 (71.50→75.33)"
      },
      "operator_class": "scatter-update",
      "precision": "全 20 例过",
      "speedup": 18.0,
      "task_dir": "task_scatter_20260821_180115_5c6355f3"
    },
    {
      "comparison_sha256": "5d78fa8b25e1be4c43ca957cd0de67e68691103e5de562a8de25b8f8d52bfc11",
      "decision_sha256": "87dcaf8f61417c078f158abc2bfb490e4493a71cf78ab9071372b6ed0f14cbb1",
      "operator_class": "scatter-update",
      "performance_sha256": "8907b32ac4c27a14926476c313d3ccd104a5e9faadea0c824a806a066944209b",
      "round": 4,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "f7d9bd72b0817c0419749966763daef5194f680e41e729c65b742c9a1d09369f",
      "verify_sha256": "776470b01acf3a2f38fe97366baa6d41cbbf7ddf33434b4f582a4b1e0a25887e"
    }
  ],
  "evidence_strength": "case4: 426502us→1281us (333x), case18: 779us→42.9us (18x), 均快于基线",
  "feature_signature": {
    "bottleneck": [
      "dk-split",
      "scalar-remap",
      "simt-cache-stale"
    ],
    "dtypes": [
      "fp16",
      "bf16"
    ],
    "pattern": "scatter-write-add-reduce",
    "reduce_mode": "add",
    "structure": [
      "scatter",
      "indexed-write",
      "atomic-reduce",
      "fp32-workspace"
    ]
  },
  "gain": "333x / 18x",
  "generality": "op_class",
  "id": "S1-GmAddWs",
  "implementation_steps": [
    "将 data 批量转换为 fp32 并写入 workspace，作为散射累加初值",
    "完成核间同步后使用 SIMT fp32 原子加更新 workspace",
    "执行 asc_threadfence 与 SyncAll 保证写可见，再将 workspace 单次转换回输出 dtype"
  ],
  "instance_ids": [],
  "intent": "消除低精度散射加分段路径中的标量地址重映射和逐更新 GM read-modify-write，同时避免多次低精度舍入。",
  "mechanism": "GM fp32 workspace 原子累加三段式：Pass1 data→fp32 workspace（bulk cast-copy）→ SyncAll → SIMT fp32 原子累加 → Pass3 fp32→DX 回写 y。关键：VF 内 asc_threadfence() + Pass2 后 SyncAll 保证 SIMT 写对后续 MTE 读可见（否则全部更新丢失）。",
  "name": "低精度散射加的 FP32 工作区原子累加",
  "needs_human_review": false,
  "op": "scatter",
  "operator_class": "scatter-update",
  "operator_scope": "存在重复索引、归约模式为加法且输出为 fp16/bf16 的 scatter-update 数据流",
  "principle": "把低精度散射加提升为 fp32 workspace 上的 GM 原子累加，使每个更新直接定位目标元素，既绕过 D/K-split 标量 remap，又把低精度多次舍入变为末尾一次舍回。",
  "provenance": {
    "final_summary": "opt/final_summary.json",
    "opt_md": "scatter_opt.md",
    "state_md": "STATE.md",
    "task_dir": "task_scatter_20260821_180115_5c6355f3"
  },
  "related_anti_patterns": [
    "dk-split-scalar-address-remap",
    "simt-write-mte-read-visibility-gap"
  ],
  "related_seed_ids": [
    "S1"
  ],
  "review_reason": "",
  "risks": [
    "workspace 可能达到数百 MB；遗漏 threadfence 或核间同步会使后续 MTE 读取陈旧数据并静默丢失更新"
  ],
  "schema_version": 2,
  "slug": "gm-fp32-workspace-atomic-add",
  "source": "task_dir",
  "status": "applied",
  "summary": "使用 FP32 GM 工作区完成 Scatter 低精度 add 原子累加，并在末尾一次舍回。",
  "verification": {
    "correctness": [
      "覆盖重复索引、高冲突、fp16/bf16 边界值，并执行全量精度验证确认累加结果完整"
    ],
    "performance": [
      "比较高开销分段路径与常规路径的多组 shape 中位耗时，并计入 workspace 初始化和回写成本"
    ],
    "rollback_signals": [
      "出现更新丢失、workspace 超预算、非目标 dtype 误路由或代表性 shape 稳定回归时回退"
    ]
  },
  "verified_by": "task_scatter_20260821_180115_5c6355f3"
}
-->

# 性能优化策略：低精度散射加的 FP32 工作区原子累加

单一优化点：使用 FP32 GM 工作区完成 Scatter 低精度 add 原子累加，并在末尾一次舍回。

## 1. 原理

把低精度散射加提升为 fp32 workspace 上的 GM 原子累加，使每个更新直接定位目标元素，既绕过 D/K-split 标量 remap，又把低精度多次舍入变为末尾一次舍回。

实现机制：GM fp32 workspace 原子累加三段式：Pass1 data→fp32 workspace（bulk cast-copy）→ SyncAll → SIMT fp32 原子累加 → Pass3 fp32→DX 回写 y。关键：VF 内 asc_threadfence() + Pass2 后 SyncAll 保证 SIMT 写对后续 MTE 读可见（否则全部更新丢失）。

## 2. 性能问题模式

- 优化目标：消除低精度散射加分段路径中的标量地址重映射和逐更新 GM read-modify-write，同时避免多次低精度舍入。
- 适用数据流：存在重复索引、归约模式为加法且输出为 fp16/bf16 的 scatter-update 数据流
- Feature signature：`{"bottleneck": ["dk-split", "scalar-remap", "simt-cache-stale"], "dtypes": ["fp16", "bf16"], "pattern": "scatter-write-add-reduce", "reduce_mode": "add", "structure": ["scatter", "indexed-write", "atomic-reduce", "fp32-workspace"]}`

## 3. 正确性红线

- workspace 可能达到数百 MB；遗漏 threadfence 或核间同步会使后续 MTE 读取陈旧数据并静默丢失更新

资源与硬件约束：

- 必须预留 numel×4B 的 fp32 workspace，并在 host tiling 与 GetWorkspaceSize 中使用相同判据

## 4. 泛化条件

- 策略作用域：op_class：scatter-update

适用：

- Scatter reduce 模式为 add，输出 dtype 为 fp16 或 bf16，且低精度直接累加不能满足精度要求

不适用：

- 非 add 归约、workspace 不足或无法提供 fp32 GM 原子加与写后可见性保证时禁止启用

## 5. 实施步骤

1. 将 data 批量转换为 fp32 并写入 workspace，作为散射累加初值
2. 完成核间同步后使用 SIMT fp32 原子加更新 workspace
3. 执行 asc_threadfence 与 SyncAll 保证写可见，再将 workspace 单次转换回输出 dtype

## 6. LLM 前置问题

- 目标实现是否满足：Scatter reduce 模式为 add，输出 dtype 为 fp16 或 bf16，且低精度直接累加不能满足精度要求？
- 是否命中排除条件：非 add 归约、workspace 不足或无法提供 fp32 GM 原子加与写后可见性保证时禁止启用？

## 7. 验收标准

正确性：

- 覆盖重复索引、高冲突、fp16/bf16 边界值，并执行全量精度验证确认累加结果完整

性能：

- 比较高开销分段路径与常规路径的多组 shape 中位耗时，并计入 workspace 初始化和回写成本

回滚信号：

- 出现更新丢失、workspace 超预算、非目标 dtype 误路由或代表性 shape 稳定回归时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：dk-split-scalar-address-remap, simt-write-mte-read-visibility-gap

- task_scatter_20260821_180115_5c6355f3（case=4, speedup=333.0）
- task_scatter_20260821_180115_5c6355f3（case=18, speedup=18.0）
- scatter-20260831_151225-664ffa（round=4, status=accepted）

## 检索卡（短卡）

动作：将低精度散射加改为 fp32 workspace 上的 GM 原子累加，并把多次低精度舍入改为末尾一次舍回。
适用：scatter reduce 为 add，输出为 fp16 或 bf16，且低精度直接累加不满足精度要求。
限制：排除非 add 归约和 workspace 不足；必须执行 threadfence 与核间同步以避免陈旧读取和丢更新。
范围：scatter-reduce 的 fp16/bf16 加法归约路径。
检索词：fp32 workspace、SIMT fp32 原子加、GetValue/SetValue、asc_threadfence、D/K-split。
机会：存在重复索引，D/K-split 路径仍逐元素 GetValue/SetValue 中转并发生多次低精度舍入。
代价：workspace 可能达到数百 MB。
