---
type: Optimization
title: 极值与索引回溯的全向量归约
description: 用向量极值、相等掩码和位置编码完成 argmax/argmin 的值与索引归约。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/vectorized-arg-index-reduce.md
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
      "候选值、位置编码和中间掩码必须同时满足 UB 容量与向量 API 对齐要求",
      "比较与索引回溯必须显式实现算子的 NaN、并列值和低精度提升规则"
    ],
    "excluded_conditions": [
      "索引无法编码进精确可比较的片上类型，或归约语义依赖稳定的全序但硬件比较不能表达时不适用",
      "归约长度很短且标量路径没有形成瓶颈时，额外向量回溯可能无收益"
    ],
    "required_conditions": [
      "目标同时输出极值和其位置，且归约轴可连续或规则分块读取",
      "每个 slice 的候选能够在片上完成向量极值归约与相等掩码构造",
      "host 能为通用路径和向量路径选择安全的 tiling"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-23",
  "evidence": [
    {
      "after_us": 421.6,
      "before_us": 1370.2,
      "case": "1",
      "operator_class": "sort-select",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/arg_max/<run-id>/phase6_apply/final_report.md",
      "speedup": 3.25,
      "status": "accepted"
    },
    {
      "comparison_sha256": "cee08505d286ccc4d0964bf0de6b74d9f31077da8990bad190aa0fbaf4d8b471",
      "decision_sha256": "ea99974916c9179a7812b97bd65f73a07f1ca81b005fec9964c8f5c31bd54854",
      "operator_class": "sort-select",
      "performance_sha256": "26eb5adbcf0655b1a5c0d5364c17a273d38972f5f12f08d30a32a548ec7951df",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "6d48047f5369bc20b9913f68bf3a9e11c70aa5553553027bb8ba34373a46bfd8",
      "verify_sha256": "26e70eed3e30db9698d383178fff902fde1f99aedf31352e5fce4893a64aa7e2"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-index-recovery",
      "per-block-sync"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "vectorized-arg-index-reduce",
    "reduce_mode": "argmax-argmin",
    "structure": [
      "vector-reduce",
      "mask",
      "index-traceback"
    ]
  },
  "gain": "case_1 1370.2→421.6us，3.25x；独立 K-Search 复现 3.27x。",
  "generality": "op_class",
  "id": "ARGRED-001",
  "implementation_steps": [
    "按 slice 分配核与 UB tile，把输入值提升到满足比较精度的类型",
    "以向量 ReduceMax/ReduceMin 维护运行极值，避免在每个块上 GetValue 到标量流水",
    "用极值相等掩码与位置编码执行向量索引归约，并按契约选择最小或最大并列索引",
    "每个 slice 只在最终结果处执行必要的 V→S 可见性同步与标量写回",
    "为 NaN、空 slice、不支持 dtype 和资源不足场景保留已验证回退路径"
  ],
  "intent": "消除 arg-reduce 中逐块标量取值、索引扫描和全流水同步，使值归约与索引恢复都留在向量流水。",
  "mechanism": "向量流水先生成运行极值，再通过 EQ 掩码把命中 lane 映射为位置编码，并对编码执行 ReduceMin/ReduceMax 得到契约要求的 winner；整个 slice 仅在最终结果处从向量域转到标量域。",
  "name": "极值与索引回溯的全向量归约",
  "op": "arg_max",
  "operator_class": "sort-select",
  "operator_scope": "同时返回极值及索引、且归约轴可规则分块的 argmax/argmin 类选择归约",
  "principle": "逐块把极值取回标量会串行化向量归约并重复支付同步成本；将值比较、命中判断和位置选择统一编码为向量归约，可把同步次数降到每个输出 slice 一次。",
  "provenance": {
    "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/arg_max/<run-id>/phase6_apply/final_report.md"
  },
  "related_anti_patterns": [
    "per-row-pipebarrier-sync"
  ],
  "risks": [
    "NaN 与并列值处理不一致会产生看似合理但索引错误的静默精度问题",
    "位置编码在长轴上可能超出低精度整数或浮点的精确表示范围"
  ],
  "schema_version": 2,
  "slug": "vectorized-arg-index-reduce",
  "source": "external_verified",
  "status": "applied",
  "summary": "用向量极值、相等掩码和位置编码完成 argmax/argmin 的值与索引归约。",
  "verification": {
    "correctness": [
      "覆盖首/尾命中、全相等、重复极值、NaN、Inf、尾 tile 与不同低精度输入，并核对索引契约"
    ],
    "performance": [
      "分别测量长短归约轴，确认 GetValue 和逐块 PIPE_ALL 消失，并以多次冷缓存中位数比较"
    ],
    "rollback_signals": [
      "任一 NaN/并列语义错误、位置编码溢出、设备异常或短轴稳定回归时回退"
    ]
  }
}
-->

# 性能优化策略：极值与索引回溯的全向量归约

单一优化点：用向量极值、相等掩码和位置编码完成 argmax/argmin 的值与索引归约。

## 1. 原理

逐块把极值取回标量会串行化向量归约并重复支付同步成本；将值比较、命中判断和位置选择统一编码为向量归约，可把同步次数降到每个输出 slice 一次。

实现机制：向量流水先生成运行极值，再通过 EQ 掩码把命中 lane 映射为位置编码，并对编码执行 ReduceMin/ReduceMax 得到契约要求的 winner；整个 slice 仅在最终结果处从向量域转到标量域。

## 2. 性能问题模式

- 优化目标：消除 arg-reduce 中逐块标量取值、索引扫描和全流水同步，使值归约与索引恢复都留在向量流水。
- 适用数据流：同时返回极值及索引、且归约轴可规则分块的 argmax/argmin 类选择归约
- Feature signature：`{"bottleneck": ["scalar-index-recovery", "per-block-sync"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "vectorized-arg-index-reduce", "reduce_mode": "argmax-argmin", "structure": ["vector-reduce", "mask", "index-traceback"]}`

## 3. 正确性红线

- NaN 与并列值处理不一致会产生看似合理但索引错误的静默精度问题
- 位置编码在长轴上可能超出低精度整数或浮点的精确表示范围

资源与硬件约束：

- 候选值、位置编码和中间掩码必须同时满足 UB 容量与向量 API 对齐要求
- 比较与索引回溯必须显式实现算子的 NaN、并列值和低精度提升规则

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- 目标同时输出极值和其位置，且归约轴可连续或规则分块读取
- 每个 slice 的候选能够在片上完成向量极值归约与相等掩码构造
- host 能为通用路径和向量路径选择安全的 tiling

不适用：

- 索引无法编码进精确可比较的片上类型，或归约语义依赖稳定的全序但硬件比较不能表达时不适用
- 归约长度很短且标量路径没有形成瓶颈时，额外向量回溯可能无收益

## 5. 实施步骤

1. 按 slice 分配核与 UB tile，把输入值提升到满足比较精度的类型
2. 以向量 ReduceMax/ReduceMin 维护运行极值，避免在每个块上 GetValue 到标量流水
3. 用极值相等掩码与位置编码执行向量索引归约，并按契约选择最小或最大并列索引
4. 每个 slice 只在最终结果处执行必要的 V→S 可见性同步与标量写回
5. 为 NaN、空 slice、不支持 dtype 和资源不足场景保留已验证回退路径

## 6. LLM 前置问题

- 目标实现是否满足：目标同时输出极值和其位置，且归约轴可连续或规则分块读取？
- 目标实现是否满足：每个 slice 的候选能够在片上完成向量极值归约与相等掩码构造？
- 目标实现是否满足：host 能为通用路径和向量路径选择安全的 tiling？
- 是否命中排除条件：索引无法编码进精确可比较的片上类型，或归约语义依赖稳定的全序但硬件比较不能表达时不适用？

## 7. 验收标准

正确性：

- 覆盖首/尾命中、全相等、重复极值、NaN、Inf、尾 tile 与不同低精度输入，并核对索引契约

性能：

- 分别测量长短归约轴，确认 GetValue 和逐块 PIPE_ALL 消失，并以多次冷缓存中位数比较

回滚信号：

- 任一 NaN/并列语义错误、位置编码溢出、设备异常或短轴稳定回归时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：per-row-pipebarrier-sync

- ksearch-arg-max-<run-id>（status=accepted, case=1, speedup=3.25）
- arg_max-<run-id>（round=1, status=accepted）

## 检索卡（短卡）

动作：将逐块标量取值、命中与位置选择改为向量归约，使值归约和索引恢复留在向量流水，每个输出 slice 同步一次
适用：同时输出极值及其位置，且归约轴可连续或规则分块读取
限制：候选值、位置编码及掩码须满足UB容量和API对齐；保持NaN/并列规则，并核对长轴位置编码范围
范围：selection-reduce 的 arg-reduce 输出 slice
检索词：向量归约、ReduceMax/ReduceMin、GetValue、EQ 掩码、UB tile
机会：arg-reduce 中仍有逐块标量取值、索引扫描或全流水同步
