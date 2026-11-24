---
type: Optimization
title: deferred k 端归一化 + fp32 域直排的链路精简（小幅净增益档）
description: 在整行向量排序选择已生效的 dataflow 上，把归一化推迟到 k 端（只对 k 个输出归一化）、排序/键构造留在 fp32 值域并移除 dtype 域复合键构造、host 行块参数相应调整的链路精简；实测为小幅净增益档（增量略 >1、零回归、官方判据全过、净删百余行）。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/deferred-k-norm-fp32-domain-cleanup.md
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
      "机制级强假设已证伪：整行排序支配期（vec issue ≥90%）下，移除每行十余条向量指令/延迟归一化仅 -0.8% vec 时间，头部 case 增量 <1.15x（预注册证伪条款触发）；本卡只主张 cleanup 档净增益",
      "批量归约 intrinsic（WholeReduce*/ReduceSum<AR> 类）在本 dataflow 两次独立 probe 均 NO-GO（其一 0.91x 回归）：链路归约保持 per-chunk/per-row 链式，不换批量原语",
      "UB 预算按新数据通路逐项核算（host tiling 与 kernel Init 一致）"
    ],
    "excluded_conditions": [
      "排序本身已被替换/剪枝（此时每行指令量重新成为一阶项，本边界不适用）"
    ],
    "required_conditions": [
      "适用于判断『是否值得做』：整行排序选择已生效且 profiling 显示 vec issue 占比 ≥90%、时间与每行向量指令数弱相关"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "9db820c2569989e61a05a5965759e613d2490ed6ce14845788770ef06750e917",
      "decision_sha256": "00ae1ed6c2f423273382c0dfc4f041de1d92a8e72ac7fce9e8b9473ddcad9adc",
      "incremental_sha256": "2dd1981b751ffe0fa43923505d1a69f631b579b951340dc367c8910fa7a35939",
      "operator_class": "layout-transform",
      "performance_sha256": "7d1cc34ae643df8bbfbd0242ac71eb49fea85ba36ed581f1cef84bb536592959",
      "precision": "官方判据 20/20 PASS",
      "probe_sha256": "5302a2cd593923618147d61b8a0b9ef49a01239820c468451f6c143e3bdff90e",
      "round": 3,
      "run_id": "<run-id>",
      "speedup": "机制证伪（c3 1.0073<1.15 ∧ c10 1.0664<1.15 预注册条款触发，vec 仅 -0.8%）；精简版增量 1.0171x 接受保留；P1 批量归约 probe NO-GO（c3 1.044x<1.25、c10 0.910x 回归）",
      "status": "accepted",
      "strategy_sha256": "4a7092d961718ca2170ea23ea81bcdca2d2b494b59e6a3c4ca2bd89120e68a1f",
      "verify_sha256": "79b58310cf2a402781ed4be87c258d4f800f4748ae82f74dafb8a6950aa65f6a"
    },
    {
      "comparison_sha256": "9db820c2569989e61a05a5965759e613d2490ed6ce14845788770ef06750e917",
      "decision_sha256": "00ae1ed6c2f423273382c0dfc4f041de1d92a8e72ac7fce9e8b9473ddcad9adc",
      "operator_class": "layout-transform",
      "performance_sha256": "7d1cc34ae643df8bbfbd0242ac71eb49fea85ba36ed581f1cef84bb536592959",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "4a7092d961718ca2170ea23ea81bcdca2d2b494b59e6a3c4ca2bd89120e68a1f",
      "verify_sha256": "79b58310cf2a402781ed4be87c258d4f800f4748ae82f74dafb8a6950aa65f6a"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "whole-row-sort-vpipe-bound"
    ],
    "dtypes": [
      "fp16",
      "fp32",
      "bf16"
    ],
    "pattern": "sort-cycle-dominated"
  },
  "generality": "op_class",
  "id": "DEFERRED-K-NORM-FP32-CLEANUP",
  "implementation_steps": [
    "用 op_summary 确认 vec issue 占比与每行指令量-时间弱相关",
    "如仍要验证：预注册证伪阈值 → 最小 probe（先 A/B 后全量）→ 采集后按条款裁决",
    "机制证伪时评估精简版是否有无回归的小幅净增益，可接受保留但边界如实记录"
  ],
  "intent": "界定『选择机制摊平后继续削向量指令量/换归约原语』这类候选的真实收益边界，避免在排序支配期重复投入。",
  "mechanism": "证伪实验：fp32 域值排序 + deferred k-only normalize（移除 dtype 域复合键构造、归一化推迟到 k 端）完整实现后，目标 case 增量未达预注册阈值（两个头部 case 均 <1.15x，vec 时间仅 -0.8%）；两轮独立 probe（S3-P1 ReduceSum<AR>+Brcb、S5-P1 WholeReduceMax/Sum+fold）均 NO-GO（其一 0.91x 回归）。",
  "name": "deferred k 端归一化 + fp32 域直排的链路精简（小幅净增益档）",
  "operator_class": "layout-transform",
  "operator_scope": "整行向量排序选择已生效、AIV vec 占比 ≥90% 的选择类 dataflow",
  "principle": "整行排序成本由排序网络/基选的固定 V-pipe 通行数决定，与每行少量附加向量指令近似无关；批量归约 intrinsic 的每迭代多次全管线同步在小行块下无法摊薄，反而慢于链式 per-chunk 归约。",
  "related_anti_patterns": [],
  "risks": [
    "把 cleanup 级小增益误读为机制有效（须看 vec 时间是否真的下降）",
    "批量归约 intrinsic 在小行块下的同步成本被低估"
  ],
  "slug": "deferred-k-norm-fp32-domain-cleanup",
  "summary": "在整行向量排序选择已生效的 dataflow 上，把归一化推迟到 k 端（只对 k 个输出归一化）、排序/键构造留在 fp32 值域并移除 dtype 域复合键构造、host 行块参数相应调整的链路精简；实测为小幅净增益档（增量略 >1、零回归、官方判据全过、净删百余行）。同轮证伪了其机制级强假设（详见 constraints）：这类精简不会解锁排序支配期的 cycle 收益。",
  "verification": {
    "correctness": [
      "精简版官方判据全过（本轮 20/20，y ≤1 ulp、row_idx/哨兵 exact、全平局 case 位级 0 差）"
    ],
    "performance": [
      "增量 total_speedup>1.0 且控制 case 无超阈值回归（本轮 1.0171x；期望只按 cleanup 档设定，不按机制档）",
      "若头部 case 增量显著超 1.15x 才可升级为机制级主张（本轮未达成，如实记 falsified）"
    ],
    "rollback_signals": [
      "任何官方判据失配或稳定控制 case 回归超阈值"
    ]
  }
}
-->

# 性能优化策略：deferred k 端归一化 + fp32 域直排的链路精简（小幅净增益档）

单一优化点：在整行向量排序选择已生效的 dataflow 上，把归一化推迟到 k 端（只对 k 个输出归一化）、排序/键构造留在 fp32 值域并移除 dtype 域复合键构造、host 行块参数相应调整的链路精简；实测为小幅净增益档（增量略 >1、零回归、官方判据全过、净删百余行）。同轮证伪了其机制级强假设（详见 constraints）：这类精简不会解锁排序支配期的 cycle 收益。

## 1. 原理

整行排序成本由排序网络/基选的固定 V-pipe 通行数决定，与每行少量附加向量指令近似无关；批量归约 intrinsic 的每迭代多次全管线同步在小行块下无法摊薄，反而慢于链式 per-chunk 归约。

实现机制：证伪实验：fp32 域值排序 + deferred k-only normalize（移除 dtype 域复合键构造、归一化推迟到 k 端）完整实现后，目标 case 增量未达预注册阈值（两个头部 case 均 <1.15x，vec 时间仅 -0.8%）；两轮独立 probe（S3-P1 ReduceSum<AR>+Brcb、S5-P1 WholeReduceMax/Sum+fold）均 NO-GO（其一 0.91x 回归）。

## 2. 性能问题模式

- 优化目标：界定『选择机制摊平后继续削向量指令量/换归约原语』这类候选的真实收益边界，避免在排序支配期重复投入。
- 适用数据流：整行向量排序选择已生效、AIV vec 占比 ≥90% 的选择类 dataflow
- Feature signature：`{"bottleneck": ["whole-row-sort-vpipe-bound"], "dtypes": ["fp16", "fp32", "bf16"], "pattern": "sort-cycle-dominated"}`

## 3. 正确性红线

- 把 cleanup 级小增益误读为机制有效（须看 vec 时间是否真的下降）
- 批量归约 intrinsic 在小行块下的同步成本被低估

资源与硬件约束：

- 机制级强假设已证伪：整行排序支配期（vec issue ≥90%）下，移除每行十余条向量指令/延迟归一化仅 -0.8% vec 时间，头部 case 增量 <1.15x（预注册证伪条款触发）；本卡只主张 cleanup 档净增益
- 批量归约 intrinsic（WholeReduce*/ReduceSum<AR> 类）在本 dataflow 两次独立 probe 均 NO-GO（其一 0.91x 回归）：链路归约保持 per-chunk/per-row 链式，不换批量原语
- UB 预算按新数据通路逐项核算（host tiling 与 kernel Init 一致）

## 4. 泛化条件

- 策略作用域：op_class：layout-transform

适用：

- 适用于判断『是否值得做』：整行排序选择已生效且 profiling 显示 vec issue 占比 ≥90%、时间与每行向量指令数弱相关

不适用：

- 排序本身已被替换/剪枝（此时每行指令量重新成为一阶项，本边界不适用）

## 5. 实施步骤

1. 用 op_summary 确认 vec issue 占比与每行指令量-时间弱相关
2. 如仍要验证：预注册证伪阈值 → 最小 probe（先 A/B 后全量）→ 采集后按条款裁决
3. 机制证伪时评估精简版是否有无回归的小幅净增益，可接受保留但边界如实记录

## 6. LLM 前置问题

- 目标实现是否满足：适用于判断『是否值得做』：整行排序选择已生效且 profiling 显示 vec issue 占比 ≥90%、时间与每行向量指令数弱相关？
- 是否命中排除条件：排序本身已被替换/剪枝（此时每行指令量重新成为一阶项，本边界不适用）？

## 7. 验收标准

正确性：

- 精简版官方判据全过（本轮 20/20，y ≤1 ulp、row_idx/哨兵 exact、全平局 case 位级 0 差）

性能：

- 增量 total_speedup>1.0 且控制 case 无超阈值回归（本轮 1.0171x；期望只按 cleanup 档设定，不按机制档）
- 若头部 case 增量显著超 1.15x 才可升级为机制级主张（本轮未达成，如实记 falsified）

回滚信号：

- 任何官方判据失配或稳定控制 case 回归超阈值

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- moe_gating_top_k_softmax-20260901_132104-d2096f（round=3, status=accepted, speedup=机制证伪（c3 1.0073<1.15 ∧ c10 1.0664<1.15 预注册条款触发，vec 仅 -0.8%）；精简版增量 1.0171x 接受保留；P1 批量归约 probe NO-GO（c3 1.044x<1.25、c10 0.910x 回归））
- moe_gating_top_k_softmax-20260901_132104-d2096f（round=3, status=accepted）

## 检索卡（短卡）

动作：把归一化推迟到 k 端只对 k 个输出归一化，排序与键构造留在 fp32 值域并移除 dtype 域复合键构造
适用：整行排序选择已生效且 profiling 显示 vec issue 占比 >=90%、时间与每行向量指令数弱相关
限制：只主张 cleanup 档净增益，头部 case 增量 <1.15x 即机制级假设证伪；链路归约保持 per-chunk/per-row 链式
范围：layout-transform 的整行向量排序选择 dataflow
检索词：deferred k-norm、fp32 值域直排、复合键构造、vec issue 占比、WholeReduce、cleanup 档
机会：整行排序支配期（vec issue >=90%）下削每行向量指令量只换来 -0.8% vec 时间
