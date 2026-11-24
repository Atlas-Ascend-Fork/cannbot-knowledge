---
type: Optimization
title: 不变量外提：批内重复生成的权重表 Init 期一次生成常驻 UB
description: 把每 (m,wc,i0) 批重复生成的 covH 权重改为 Init 期一次生成常驻 UB 表，批内改偏移 BRC 读。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/covh-init-precompute-ub-resident.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "常驻表须设容量守卫（本 run AlignUp256(H*4) <= 8KB），超限自动回退原逐批生成路径以保通用性",
      "表内容必须与逐批生成逐位同值（本 run covH 仅依赖全核不变量 (k,s,p,hOut) 与行号，与批号/核号无关）",
      "常驻表须计入 UB 固定预算（本 run 计入 fixedBytes 并参与 R 预算推导），否则 R 推导会越界",
      "广播读取的 4B 对齐地址序列须保持不变（i0 偏移读）"
    ],
    "excluded_conditions": [
      "权重依赖批内变量（批号、核号、运行时状态）时不适用——外提的前提是全 H 不变量",
      "H 极大导致表超出容量守卫时不适用，会走回退路径（无收益但也无回退）",
      "UB 余量本已紧张、常驻表会挤压 R（批深）时不适用——本 run 全部 20 case H∈[63,511]、表最大 2KB、UB 余量 >85% 才成立"
    ],
    "required_conditions": [
      "profiling 显示 scalar 仍为剩余主 pacing（本 run 10 决策 case scalar 15.36us pacing 8/10：case5 0.987 / case4 0.975 / case2 0.948）",
      "权重生成在每 (m,wc,i0) 批内重复付出：VF 包装的 scalar 发射 + ~14 条矢量指令 + 批内累加前的串行前置",
      "权重只依赖全核不变量与行号（本 run covH 依赖 (k,s,p,hOut) 与行号），全 H 表 + i0 偏移读与逐批生成逐位同值",
      "代码库已存在同类外提先例作为不对称证据（本 run covW 已 Init 外提，covH 逐批重算是剩余的不对称项）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 13.6193,
      "before_us": 14.6661,
      "operator": "unfold_mean",
      "operator_class": "reduction",
      "pairs": 10,
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "session_ids": ["ses_f78fb4bc0ffeUuJVQ39KBaOFdF", "ses_f787a6962ffe6ejU9OzHK9PKxR"],
      "speedup": 1.0769,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-pipe-pacing",
      "per-batch-weight-regeneration",
      "batch-fixed-overhead"
    ],
    "pattern": "invariant-hoisting-ub-resident-table",
    "structure": [
      "init-phase-precompute",
      "whole-invariant-table",
      "capacity-guard-with-fallback",
      "offset-based-brc-read"
    ]
  },
  "generality": "op_class",
  "id": "UM-COVH-INIT-PRECOMPUTE-UB-RESIDENT",
  "implementation_steps": [
    "op_kernel: 新增 TBuf covHAll_ + bool covHAllReady_ 成员",
    "Init: covHTableBytes=AlignUp256(H*4) <= 8KB 守卫置 covHAllReady_ 并计入 fixedBytes（R 预算推导）；InitBuffer(covHAll_)；Init 末尾 GenCovWChunkVF(covHAll, jBase=0, hPad, ..., hOut) 全 H 一次闭式生成",
    "ComputeMainRow/ComputeSplitPartial: i0 批内 covHAllReady_ 时 AccumRowCovHBatchVF(accVec, xUb, covHAll_.Get<float>()[i0], ...)（BRC 4B 对齐地址序列不变），否则走原逐批 GenCovWChunkVF(covHArr_, i0, rCnt,...) 回退路径（逐位等价）",
    "常驻表计入 UB 固定预算，重新核对 R（批深）推导"
  ],
  "intent": "把每 (m,wc,i0) 批重复生成的 covH 权重（VF 包装 scalar 发射 + ~14 条矢量指令 + 批内累加前的串行前置）外提到 Init 期一次生成常驻 UB，批内改为偏移读，消除重复生成与它带来的批内串行前置。",
  "mechanism": "covH 权重不变量外提：Init 期全 H 一次闭式生成常驻 UB 表（<=8KB 守卫，超限回退原逐批生成路径），批内 AccumRowCovHBatchVF 直接 covHAll[i0] 偏移 BRC_B32 读，消除每 (m,wc,i0) 批 GenCovWChunkVF 重生成。",
  "name": "不变量外提：批内重复生成的权重表 Init 期一次生成常驻 UB",
  "operator_class": "reduction",
  "operator_scope": "逐批重复生成常量权重/系数表的累加类算子：权重只依赖全核不变量与行号、表规模落在 UB 守卫内、批内生成含 VF 包装 scalar 发射与串行前置",
  "principle": "逐批重算不变量的代价不止是指令数，更是它在批内累加之前的串行前置——外提后不仅省掉生成指令，批内累加流也变为连续。判定前提是该量对所有批取值相同（只依赖全核不变量），此时「全表 + 偏移读」与「逐批生成」逐位同值，数值零风险。容量守卫与回退路径是该机制保持通用性的必要条件。",
  "related_anti_patterns": [],
  "risks": [
    "常驻表占用 UB 固定预算，会挤压 R（批深）；H 大或 UB 余量紧的算子需重新对账，本 run 全部 20 case 表最大 2KB、UB 余量 >85% 才安全",
    "守卫阈值设得过宽会在极端 H 下越界，过窄则丢失收益",
    "回退路径必须保持逐位等价，否则回退场景静默出错"
  ],
  "slug": "covh-init-precompute-ub-resident",
  "summary": "covH 权重不变量外提：Init 期全 H 一次闭式生成常驻 UB 表（<=8KB 守卫，超限回退原逐批生成路径），批内 AccumRowCovHBatchVF 直接 covHAll[i0] 偏移 BRC_B32 读，消除每 (m,wc,i0) 批 GenCovWChunkVF 重生成（VF 包装 scalar 发射 + ~14 条矢量指令 + 批内累加前串行前置）。kernel geomean 14.6661→13.6193（x1.0769）；scalar -14.6%、vec -36.9%。",
  "verification": {
    "correctness": [
      "精度 20/20 PASS（evidence_run/rounds/round_01/accuracy/candidate_test_unfold_mean.log）",
      "逐位同值论证：covH 只依赖全核不变量 (k,s,p,hOut) 与行号，全 H 表 + i0 偏移读与逐批生成逐位相同；累加次序不变、零新跨流水同步",
      "编译修复 0/3、精度修复 0/3（本 run 无修复消耗）"
    ],
    "performance": [
      "形式化性能 10 对平衡交替（同 shape、溯源干净、制品切换 md5 留痕）：逐对比值 1.0690-1.0822 全部 >1",
      "kernel_geomean_us 14.6661→13.6193（x1.0769）",
      "scalar 15.38→13.13us（-14.6%）、vec 10.76→6.79us（-36.9%，权重生成不仅是指令开销更是批内累加前串行点，外提后累加流连续）；重 case 最高 x1.209（case5 63.9→52.9us）",
      "champion 累计 23.738→13.6193（x1.7432，与 d001 叠加）"
    ],
    "rollback_signals": [
      "常驻表使 R 推导越界或 UB 预算超限",
      "回退路径与逐批生成不再逐位一致",
      "scalar/vec 未下降或出现未触碰域回退"
    ]
  }
}
-->

# 性能优化策略：不变量外提：批内重复生成的权重表 Init 期一次生成常驻 UB

covH 权重不变量外提：Init 期全 H 一次闭式生成常驻 UB 表（<=8KB 守卫，超限回退原逐批生成路径），批内 AccumRowCovHBatchVF 直接 covHAll[i0] 偏移 BRC_B32 读，消除每 (m,wc,i0) 批 GenCovWChunkVF 重生成（VF 包装 scalar 发射 + ~14 条矢量指令 + 批内累加前串行前置）。kernel geomean 14.6661→13.6193（x1.0769）；scalar -14.6%、vec -36.9%。

## 1. 原理

逐批重算不变量的代价不止是指令数，更是它在批内累加之前的串行前置——外提后不仅省掉生成指令，批内累加流也变为连续。判定前提是该量对所有批取值相同（只依赖全核不变量），此时「全表 + 偏移读」与「逐批生成」逐位同值，数值零风险。容量守卫与回退路径是该机制保持通用性的必要条件。

实现机制：covH 权重不变量外提：Init 期全 H 一次闭式生成常驻 UB 表（<=8KB 守卫，超限回退原逐批生成路径），批内 AccumRowCovHBatchVF 直接 covHAll[i0] 偏移 BRC_B32 读，消除每 (m,wc,i0) 批 GenCovWChunkVF 重生成。

## 2. 性能问题模式

- 优化目标：把每 (m,wc,i0) 批重复生成的 covH 权重（VF 包装 scalar 发射 + ~14 条矢量指令 + 批内累加前的串行前置）外提到 Init 期一次生成常驻 UB，批内改为偏移读，消除重复生成与它带来的批内串行前置
- 适用数据流：逐批重复生成常量权重/系数表的累加类算子：权重只依赖全核不变量与行号、表规模落在 UB 守卫内、批内生成含 VF 包装 scalar 发射与串行前置
- Feature signature：`{"bottleneck": ["scalar-pipe-pacing", "per-batch-weight-regeneration", "batch-fixed-overhead"], "pattern": "invariant-hoisting-ub-resident-table", "structure": ["init-phase-precompute", "whole-invariant-table", "capacity-guard-with-fallback", "offset-based-brc-read"]}`

## 3. 正确性红线

- 常驻表占用 UB 固定预算，会挤压 R（批深）；H 大或 UB 余量紧的算子需重新对账，本 run 全部 20 case 表最大 2KB、UB 余量 >85% 才安全
- 守卫阈值设得过宽会在极端 H 下越界，过窄则丢失收益
- 回退路径必须保持逐位等价，否则回退场景静默出错

资源与硬件约束：

- 常驻表须设容量守卫（本 run AlignUp256(H*4) <= 8KB），超限自动回退原逐批生成路径以保通用性
- 表内容必须与逐批生成逐位同值（本 run covH 仅依赖全核不变量 (k,s,p,hOut) 与行号，与批号/核号无关）
- 常驻表须计入 UB 固定预算（本 run 计入 fixedBytes 并参与 R 预算推导），否则 R 推导会越界
- 广播读取的 4B 对齐地址序列须保持不变（i0 偏移读）

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- profiling 显示 scalar 仍为剩余主 pacing（本 run 10 决策 case scalar 15.36us pacing 8/10：case5 0.987 / case4 0.975 / case2 0.948）
- 权重生成在每 (m,wc,i0) 批内重复付出：VF 包装的 scalar 发射 + ~14 条矢量指令 + 批内累加前的串行前置
- 权重只依赖全核不变量与行号（本 run covH 依赖 (k,s,p,hOut) 与行号），全 H 表 + i0 偏移读与逐批生成逐位同值
- 代码库已存在同类外提先例作为不对称证据（本 run covW 已 Init 外提，covH 逐批重算是剩余的不对称项）

不适用：

- 权重依赖批内变量（批号、核号、运行时状态）时不适用——外提的前提是全 H 不变量
- H 极大导致表超出容量守卫时不适用，会走回退路径（无收益但也无回退）
- UB 余量本已紧张、常驻表会挤压 R（批深）时不适用——本 run 全部 20 case H∈[63,511]、表最大 2KB、UB 余量 >85% 才成立

## 5. 实施步骤

1. op_kernel: 新增 TBuf covHAll_ + bool covHAllReady_ 成员
2. Init: covHTableBytes=AlignUp256(H*4) <= 8KB 守卫置 covHAllReady_ 并计入 fixedBytes（R 预算推导）；InitBuffer(covHAll_)；Init 末尾 GenCovWChunkVF(covHAll, jBase=0, hPad, ..., hOut) 全 H 一次闭式生成
3. ComputeMainRow/ComputeSplitPartial: i0 批内 covHAllReady_ 时 AccumRowCovHBatchVF(accVec, xUb, covHAll_.Get<float>()[i0], ...)（BRC 4B 对齐地址序列不变），否则走原逐批 GenCovWChunkVF(covHArr_, i0, rCnt,...) 回退路径（逐位等价）
4. 常驻表计入 UB 固定预算，重新核对 R（批深）推导

## 6. LLM 前置问题

- 目标实现是否满足：profiling 显示 scalar 仍为剩余主 pacing（本 run 10 决策 case scalar 15.36us pacing 8/10：case5 0.987 / case4 0.975 / case2 0.948）？
- 目标实现是否满足：权重生成在每 (m,wc,i0) 批内重复付出：VF 包装的 scalar 发射 + ~14 条矢量指令 + 批内累加前的串行前置？
- 目标实现是否满足：权重只依赖全核不变量与行号（本 run covH 依赖 (k,s,p,hOut) 与行号），全 H 表 + i0 偏移读与逐批生成逐位同值？
- 目标实现是否满足：代码库已存在同类外提先例作为不对称证据（本 run covW 已 Init 外提，covH 逐批重算是剩余的不对称项）？
- 是否命中排除条件：权重依赖批内变量（批号、核号、运行时状态）时不适用——外提的前提是全 H 不变量？

## 7. 验收标准

正确性：

- 精度 20/20 PASS（evidence_run/rounds/round_01/accuracy/candidate_test_unfold_mean.log）
- 逐位同值论证：covH 只依赖全核不变量 (k,s,p,hOut) 与行号，全 H 表 + i0 偏移读与逐批生成逐位相同；累加次序不变、零新跨流水同步
- 编译修复 0/3、精度修复 0/3（本 run 无修复消耗）

性能：

- 形式化性能 10 对平衡交替（同 shape、溯源干净、制品切换 md5 留痕）：逐对比值 1.0690-1.0822 全部 >1
- kernel_geomean_us 14.6661→13.6193（x1.0769）
- scalar 15.38→13.13us（-14.6%）、vec 10.76→6.79us（-36.9%，权重生成不仅是指令开销更是批内累加前串行点，外提后累加流连续）；重 case 最高 x1.209（case5 63.9→52.9us）
- champion 累计 23.738→13.6193（x1.7432，与 d001 叠加）

回滚信号：

- 常驻表使 R 推导越界或 UB 预算超限
- 回退路径与逐批生成不再逐位一致
- scalar/vec 未下降或出现未触碰域回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260909_010738-free-003（operator=unfold_mean, status=accepted, speedup=1.0769, 14.6661→13.6193us, 10 对配对）

## 检索卡（短卡）

动作：把每 (m,wc,i0) 批重复生成的 covH 权重改为 Init 期一次生成常驻 UB 表，批内改偏移 BRC 读
适用：权重只依赖全核不变量与行号，且表规模落在容量守卫内（AlignUp256(H*4)<=8KB）
限制：超限须自动回退原逐批生成路径且逐位等价；常驻表须计入 fixedBytes 参与 R 预算推导
范围：reduction 的逐批重复生成常量权重表的累加类算子
检索词：不变量外提、covHAll_、BRC_B32、偏移读、AlignUp256、fixedBytes、InitBuffer
机会：权重生成是批内累加前的串行前置，scalar 仍为剩余主 pacing
代价：常驻表占 UB 固定预算并挤压 R（批深），H 大或 UB 余量紧时须重新对账
