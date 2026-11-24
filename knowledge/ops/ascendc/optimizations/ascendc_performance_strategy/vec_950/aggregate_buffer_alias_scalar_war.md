---
type: Optimization
title: 聚合中转缓冲区同址别名（val@0/idx@0 共用 32B）导致标量写覆盖未搬出数据的 WAR
description: 单个 32B TBuf 中 val@0、idx@0：idx SetValue（PIPE_S 标量写）覆盖 val 字节后 val 才被 MTE3 DataCopyPad 读取 -> 同址 WAR 丢精度（case 13 精度失败根因）。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/aggregate-buffer-alias-scalar-war.md
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
      "不同语义字段分置独立 32B 对齐 TBuf，DataCopyPad UB 侧保持 32B 对齐"
    ],
    "excluded_conditions": [
      "读写流水明确分离且地址无重叠时无需分置（如纯标量路径或纯 DMA 路径）"
    ],
    "required_conditions": [
      "聚合中转需同时写值和索引两个语义字段",
      "存在标量 SetValue（PIPE_S）写与 DataCopyPad（MTE3）读同一缓冲的地址重叠"
    ]
  },
  "classification": "negative_boundary",
  "evidence": [
    {
      "case": "13",
      "env": {
        "device": "5",
        "op_name": "Cummin",
        "post_eval_score": 60.87859925160219,
        "pre_eval_score": 57.42744371577807,
        "score_delta": "+3.45"
      },
      "operator_class": "reduction",
      "precision": "20/20 passed after split",
      "run_id": "<run-id>",
      "status": "rejected",
      "task_dir": "cann-bench_rpy/strategies/cummin_opt_20260821"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "ub-alias-war",
      "scalar-write-dma-read"
    ],
    "pattern": "aggregate-buffer-alias-scalar-war",
    "structure": [
      "same-base-different-semantic-field",
      "scalar-setvalue",
      "mte3-datacopypad",
      "32b-alignment"
    ]
  },
  "generality": "op_class",
  "id": "NEG-AGG-BUFFER-ALIAS-WAR",
  "implementation_steps": [
    "识别聚合中转缓冲区中共享基址的不同语义字段（值/索引）",
    "核对各字段的写流水（PIPE_S 标量）与读流水（MTE3 DataCopyPad）是否地址重叠",
    "分置独立 32B 对齐 TBuf，保持 UB 侧对齐，重跑精度验证"
  ],
  "intent": "避免聚合中转缓冲中不同语义字段（值/索引）共享基址导致的标量写与 DMA 读 WAR。",
  "mechanism": "修复前：单 32B TBuf 存 val@0、idx@0，idx SetValue 覆盖 val 字节，随后 MTE3 读到被覆盖的 val。修复：分置两个 32B 对齐 TBuf（val/idx 各自 @0），DataCopyPad UB 侧保持 32B 对齐。",
  "name": "聚合中转缓冲区同址别名（val@0/idx@0 共用 32B）导致标量写覆盖未搬出数据的 WAR",
  "operator_class": "reduction",
  "operator_scope": "reduction 跨核归约聚合写路径中，同一 UB 缓冲内不同语义字段（值/索引）共用基址，且存在标量 SetValue（PIPE_S）写与 MTE3 DataCopyPad 读的地址重叠",
  "principle": "同一 UB 缓冲内不同语义字段共用基址时，标量写（PIPE_S SetValue）与 DMA 读（MTE3 DataCopyPad）的地址重叠需显式规避：标量写与 DMA 读的可见性由显式同步或分址保证，共用基址会让先写后读的字段被覆盖。",
  "related_anti_patterns": [],
  "risks": [
    "同一缓冲别名字段 + 标量写与 DMA 读并发 -> 静默丢精度/错误值，仅精度 gate 可能捕获，性能路径难察觉",
    "分址后若未保持 32B 对齐（DataCopyPad 对齐要求）会引入新对齐错误"
  ],
  "slug": "aggregate-buffer-alias-scalar-war",
  "summary": "单个 32B TBuf 中 val@0、idx@0：idx SetValue（PIPE_S 标量写）覆盖 val 字节后 val 才被 MTE3 DataCopyPad 读取 -> 同址 WAR 丢精度（case 13 精度失败根因）。修复：分置两个 32B 对齐 TBuf（val/idx 各自 @0），DataCopyPad UB 侧保持 32B 对齐，修复后 20/20 passed。",
  "verification": {
    "correctness": [
      "case 13 精度失败根因定位为同址 WAR；分置两个 32B 对齐 TBuf 后 20/20 passed"
    ],
    "performance": [
      "无独立性能收益：纯正确性修复，是 S-B（case 13 23.0x）可验收前提"
    ],
    "rollback_signals": [
      "任何同一缓冲别名 + 标量写/DMA 读并发复现错误值/精度失败时立即分址"
    ]
  }
}
-->

# 性能优化策略：聚合中转缓冲区同址别名（val@0/idx@0 共用 32B）导致标量写覆盖未搬出数据的 WAR

单一优化点：单个 32B TBuf 中 val@0、idx@0：idx SetValue（PIPE_S 标量写）覆盖 val 字节后 val 才被 MTE3 DataCopyPad 读取 -> 同址 WAR 丢精度（case 13 精度失败根因）。修复：分置两个 32B 对齐 TBuf（val/idx 各自 @0），DataCopyPad UB 侧保持 32B 对齐，修复后 20/20 passed。

## 1. 原理

同一 UB 缓冲内不同语义字段共用基址时，标量写（PIPE_S SetValue）与 DMA 读（MTE3 DataCopyPad）的地址重叠需显式规避：标量写与 DMA 读的可见性由显式同步或分址保证，共用基址会让先写后读的字段被覆盖。

实现机制：修复前：单 32B TBuf 存 val@0、idx@0，idx SetValue 覆盖 val 字节，随后 MTE3 读到被覆盖的 val。修复：分置两个 32B 对齐 TBuf（val/idx 各自 @0），DataCopyPad UB 侧保持 32B 对齐。

## 2. 性能问题模式

- 优化目标：避免聚合中转缓冲中不同语义字段（值/索引）共享基址导致的标量写与 DMA 读 WAR。
- 适用数据流：reduction 跨核归约聚合写路径中，同一 UB 缓冲内不同语义字段（值/索引）共用基址，且存在标量 SetValue（PIPE_S）写与 MTE3 DataCopyPad 读的地址重叠
- Feature signature：`{"bottleneck": ["ub-alias-war", "scalar-write-dma-read"], "pattern": "aggregate-buffer-alias-scalar-war", "structure": ["same-base-different-semantic-field", "scalar-setvalue", "mte3-datacopypad", "32b-alignment"]}`

## 3. 正确性红线

- 同一缓冲别名字段 + 标量写与 DMA 读并发 -> 静默丢精度/错误值，仅精度 gate 可能捕获，性能路径难察觉
- 分址后若未保持 32B 对齐（DataCopyPad 对齐要求）会引入新对齐错误

资源与硬件约束：

- 不同语义字段分置独立 32B 对齐 TBuf，DataCopyPad UB 侧保持 32B 对齐

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- 聚合中转需同时写值和索引两个语义字段
- 存在标量 SetValue（PIPE_S）写与 DataCopyPad（MTE3）读同一缓冲的地址重叠

不适用：

- 读写流水明确分离且地址无重叠时无需分置（如纯标量路径或纯 DMA 路径）

## 5. 实施步骤

1. 识别聚合中转缓冲区中共享基址的不同语义字段（值/索引）
2. 核对各字段的写流水（PIPE_S 标量）与读流水（MTE3 DataCopyPad）是否地址重叠
3. 分置独立 32B 对齐 TBuf，保持 UB 侧对齐，重跑精度验证

## 6. LLM 前置问题

- 目标实现是否满足：聚合中转需同时写值和索引两个语义字段？
- 目标实现是否满足：存在标量 SetValue（PIPE_S）写与 DataCopyPad（MTE3）读同一缓冲的地址重叠？
- 是否命中排除条件：读写流水明确分离且地址无重叠时无需分置（如纯标量路径或纯 DMA 路径）？

## 7. 验收标准

正确性：

- case 13 精度失败根因定位为同址 WAR；分置两个 32B 对齐 TBuf 后 20/20 passed

性能：

- 无独立性能收益：纯正确性修复，是 S-B（case 13 23.0x）可验收前提

回滚信号：

- 任何同一缓冲别名 + 标量写/DMA 读并发复现错误值/精度失败时立即分址

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`op_class`
- Related anti-patterns：无

- cummin-20260821（status=rejected, case=13）

## 检索卡（短卡）

动作：将聚合中转缓冲的值、索引从共享基址改为独立TBuf，规避标量写与DMA读WAR。
适用：聚合中转需同时写入值、索引两个语义字段。
限制：字段须分置独立32B对齐TBuf，DataCopyPad的UB侧保持32B对齐；禁止别名字段并发标量写与DMA读。
范围：scan-reduce跨核归约的聚合写路径。
检索词：PIPE_S SetValue、MTE3 DataCopyPad、WAR、32B对齐TBuf、缓冲别名
机会：聚合缓冲的值、索引共享基址，存在标量写与DMA读WAR。
