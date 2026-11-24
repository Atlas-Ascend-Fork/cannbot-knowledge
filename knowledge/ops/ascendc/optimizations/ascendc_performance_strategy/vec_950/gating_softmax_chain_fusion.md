---
type: Optimization
title: 归一化值链融合进选择管线（单趟 Div+舍入+复合键 + 掩码向量化 + 队列双缓冲）
description: 在向量选择机制已生效后，把 softmax 链的多趟中间值（先归一化再取键等）压成单趟：融合前置向量 pass、整块 rowSum、一趟内完成除法/位级舍入/dtype 转换并直写选择键缓冲，行索引源提升、完成掩码向量化、输出队列双缓冲，并放宽 host 行块规模上限。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/gating-softmax-chain-fusion.md
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
      "微核级控制 case（亚微秒-数微秒）同码摆动可达 ±8%，guard 低于阈值须按噪声地板记录而非判回归",
      "批量归约 intrinsic（WholeReduce*/ReduceSum<AR> 类）在本 dataflow 实测更慢（两次独立 NO-GO），链路归约应保留 per-chunk/per-row 链式"
    ],
    "excluded_conditions": [
      "归一化结果本身是输出且需与参考逐步舍入序一致时，融合须保值序列等价（否则不可上）",
      "选择管线未被摊平（vec 占比 <90%）时优先选主机制"
    ],
    "required_conditions": [
      "主选择机制已被向量/批量机制替换（否则选择循环主导，链路融合收益不可见）",
      "softmax/归一化链的中间值仅被选择阶段消费（可安全单趟化）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "90aa2f2ff2cf3efab6137877844250796a43a8edc11090c335094d45160cdddb",
      "decision_sha256": "d094fbcbd5d1f49171c8669d367f6295d9ef6b6aa3fc305b8cf32dc74d0dd1c9",
      "incremental_sha256": "9fbff3eec0c74c745ec532d7ae72adcdaa2eac3f66f3153eea961b31ed5c5b9e",
      "operator_class": "layout-transform",
      "performance_sha256": "1ace390f6456f3b3e037533ce186a1fb43f165aa68e120dd9e0570d6602a5b35",
      "precision": "官方判据 20/20 PASS（y mismatch=0 类；全平局 case y 位级 0 差）",
      "round": 2,
      "run_id": "<run-id>",
      "speedup": "incremental 1.0942x（目标 case 1.003–1.177x）；两个微核 guard case 0.89–0.92x 按噪声地板记 boundary；累计 440.29x",
      "status": "accepted",
      "strategy_sha256": "dadb32406278cc210e65aba5bd9c3c69db2dbbcd8ae41764e9556129646da20b",
      "verify_sha256": "70b2a4c61505f20a622bc62f8f015aecf52d01d6a656c16da11f385c5b4cc202"
    },
    {
      "comparison_sha256": "90aa2f2ff2cf3efab6137877844250796a43a8edc11090c335094d45160cdddb",
      "decision_sha256": "d094fbcbd5d1f49171c8669d367f6295d9ef6b6aa3fc305b8cf32dc74d0dd1c9",
      "operator_class": "layout-transform",
      "performance_sha256": "1ace390f6456f3b3e037533ce186a1fb43f165aa68e120dd9e0570d6602a5b35",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "dadb32406278cc210e65aba5bd9c3c69db2dbbcd8ae41764e9556129646da20b",
      "verify_sha256": "70b2a4c61505f20a622bc62f8f015aecf52d01d6a656c16da11f385c5b4cc202"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "ub-roundtrip-intermediates",
      "scalar-mask-per-row",
      "serialized-output-queue"
    ],
    "dtypes": [
      "fp16",
      "fp32",
      "bf16"
    ],
    "pattern": "fused-normalize-into-select-pipeline"
  },
  "generality": "op_class",
  "id": "GATING-SOFTMAX-CHAIN-FUSION",
  "implementation_steps": [
    "profiling 确认主选择已摊平、剩余瓶颈为 MTE 往返与 Scalar 杂项",
    "按数据依赖重排 softmax 链为单趟：融合向量 pass、整块 rowSum、除法+舍入+转换+键构造合一",
    "掩码/哨兵逻辑向量化；输出结构双缓冲",
    "host 放宽行块规模并重算 UB",
    "全量 verify + 增量测量（预期中小幅、无回归）"
  ],
  "intent": "消除选择机制生效后暴露的次级瓶颈：softmax 中间值的 UB 往返、逐行标量掩码与输出队列串行等待（MTE/Scalar 占比）。",
  "mechanism": "kernel：vf pass 融合（两段向量 pass 合一）、整块 rowSum、单趟 Div+RNE/Cast+复合选择键直写 topkKeyBuf、idxSrc 提升、finished 掩码向量化、输出队列双缓冲；host：F_MAX 类上限从 8 放宽到 64。",
  "name": "归一化值链融合进选择管线（单趟 Div+舍入+复合键 + 掩码向量化 + 队列双缓冲）",
  "operator_class": "layout-transform",
  "operator_scope": "exp/求和/归一化（softmax 类）与 top-k 选择融合的 gating dataflow；中间值 UB 往返和多趟标量掩码是次级瓶颈",
  "principle": "当主选择开销被向量机制摊平后，剩余时间由中间值搬运与标量杂项构成；把链路算子重排为单生产者-单消费者的一趟流（值算好即成键），中间 UB 往返与标量分支按行块批量摊薄。",
  "related_anti_patterns": [],
  "risks": [
    "值序列与参考逐步舍入序不一致造成精度失配（须位级 RNE 链）",
    "微核 case 的噪声被误判为回归"
  ],
  "slug": "gating-softmax-chain-fusion",
  "summary": "在向量选择机制已生效后，把 softmax 链的多趟中间值（先归一化再取键等）压成单趟：融合前置向量 pass、整块 rowSum、一趟内完成除法/位级舍入/dtype 转换并直写选择键缓冲，行索引源提升、完成掩码向量化、输出队列双缓冲，并放宽 host 行块规模上限。",
  "verification": {
    "correctness": [
      "官方判据全过（值输出 ≤1 dtype ulp；平局 case 位级 0 差）"
    ],
    "performance": [
      "增量 total_speedup>1 且控制 case 无超阈值回归（微核摆动按噪声地板记 boundary）"
    ],
    "rollback_signals": [
      "值输出失配",
      "稳定 case（非微核）回归超阈值",
      "增量 ≤1 且伴随 MTE/Scalar 上升"
    ]
  }
}
-->

# 性能优化策略：归一化值链融合进选择管线（单趟 Div+舍入+复合键 + 掩码向量化 + 队列双缓冲）

单一优化点：在向量选择机制已生效后，把 softmax 链的多趟中间值（先归一化再取键等）压成单趟：融合前置向量 pass、整块 rowSum、一趟内完成除法/位级舍入/dtype 转换并直写选择键缓冲，行索引源提升、完成掩码向量化、输出队列双缓冲，并放宽 host 行块规模上限。

## 1. 原理

当主选择开销被向量机制摊平后，剩余时间由中间值搬运与标量杂项构成；把链路算子重排为单生产者-单消费者的一趟流（值算好即成键），中间 UB 往返与标量分支按行块批量摊薄。

实现机制：kernel：vf pass 融合（两段向量 pass 合一）、整块 rowSum、单趟 Div+RNE/Cast+复合选择键直写 topkKeyBuf、idxSrc 提升、finished 掩码向量化、输出队列双缓冲；host：F_MAX 类上限从 8 放宽到 64。

## 2. 性能问题模式

- 优化目标：消除选择机制生效后暴露的次级瓶颈：softmax 中间值的 UB 往返、逐行标量掩码与输出队列串行等待（MTE/Scalar 占比）。
- 适用数据流：exp/求和/归一化（softmax 类）与 top-k 选择融合的 gating dataflow；中间值 UB 往返和多趟标量掩码是次级瓶颈
- Feature signature：`{"bottleneck": ["ub-roundtrip-intermediates", "scalar-mask-per-row", "serialized-output-queue"], "dtypes": ["fp16", "fp32", "bf16"], "pattern": "fused-normalize-into-select-pipeline"}`

## 3. 正确性红线

- 值序列与参考逐步舍入序不一致造成精度失配（须位级 RNE 链）
- 微核 case 的噪声被误判为回归

资源与硬件约束：

- 微核级控制 case（亚微秒-数微秒）同码摆动可达 ±8%，guard 低于阈值须按噪声地板记录而非判回归
- 批量归约 intrinsic（WholeReduce*/ReduceSum<AR> 类）在本 dataflow 实测更慢（两次独立 NO-GO），链路归约应保留 per-chunk/per-row 链式

## 4. 泛化条件

- 策略作用域：op_class：layout-transform

适用：

- 主选择机制已被向量/批量机制替换（否则选择循环主导，链路融合收益不可见）
- softmax/归一化链的中间值仅被选择阶段消费（可安全单趟化）

不适用：

- 归一化结果本身是输出且需与参考逐步舍入序一致时，融合须保值序列等价（否则不可上）
- 选择管线未被摊平（vec 占比 <90%）时优先选主机制

## 5. 实施步骤

1. profiling 确认主选择已摊平、剩余瓶颈为 MTE 往返与 Scalar 杂项
2. 按数据依赖重排 softmax 链为单趟：融合向量 pass、整块 rowSum、除法+舍入+转换+键构造合一
3. 掩码/哨兵逻辑向量化；输出结构双缓冲
4. host 放宽行块规模并重算 UB
5. 全量 verify + 增量测量（预期中小幅、无回归）

## 6. LLM 前置问题

- 目标实现是否满足：主选择机制已被向量/批量机制替换（否则选择循环主导，链路融合收益不可见）？
- 目标实现是否满足：softmax/归一化链的中间值仅被选择阶段消费（可安全单趟化）？
- 是否命中排除条件：归一化结果本身是输出且需与参考逐步舍入序一致时，融合须保值序列等价（否则不可上）？

## 7. 验收标准

正确性：

- 官方判据全过（值输出 ≤1 dtype ulp；平局 case 位级 0 差）

性能：

- 增量 total_speedup>1 且控制 case 无超阈值回归（微核摆动按噪声地板记 boundary）

回滚信号：

- 值输出失配
- 稳定 case（非微核）回归超阈值
- 增量 ≤1 且伴随 MTE/Scalar 上升

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- moe_gating_top_k_softmax-20260901_132104-d2096f（round=2, status=accepted, speedup=incremental 1.0942x（目标 case 1.003–1.177x）；两个微核 guard case 0.89–0.92x 按噪声地板记 boundary；累计 440.29x）
- moe_gating_top_k_softmax-20260901_132104-d2096f（round=2, status=accepted）

## 检索卡（短卡）

动作：把 softmax 链的多趟中间值压成单趟：一趟内完成 Div+舍入+dtype 转换并直写选择键缓冲，掩码向量化、输出队列双缓冲
适用：主选择机制已被向量/批量机制替换，且 softmax 链的中间值仅被选择阶段消费
限制：值序列须与参考逐步舍入序一致（位级 RNE 链）；批量归约 intrinsic 实测更慢，链路归约保持 per-chunk/per-row 链式
范围：layout-transform 的 softmax 与 top-k 选择融合
检索词：单趟 Div、RNE 舍入、topkKeyBuf、rowSum、finished 掩码向量化、输出队列双缓冲
机会：选择机制摊平后暴露的次级瓶颈：中间值 UB 往返、逐行标量掩码、输出队列串行等待
