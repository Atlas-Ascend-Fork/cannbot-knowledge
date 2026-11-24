---
type: Optimization
title: 固定小矩阵的跨迭代寄存器驻留
description: 让固定小矩阵跨全部归一化迭代驻留 RegTensor，仅在首尾访问 UB。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/small-matrix-register-residency.md
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
      "必须使用编译器可接受的具名 RegTensor，禁止依赖不支持的 RegTensor 数组",
      "寄存器预算需覆盖矩阵、行列统计量和临时值，并用编译结果确认没有 spill"
    ],
    "excluded_conditions": [
      "矩阵尺寸动态且超过寄存器预算、迭代逻辑含跨核依赖或编译器产生 spill 时不适用",
      "迭代次数很少或 batch 很小、kernel 启动成本占主导时收益有限"
    ],
    "required_conditions": [
      "单个小矩阵及迭代所需统计量可完整驻留向量寄存器",
      "归一化迭代只在该矩阵内部读写，轮次间无需对外可见",
      "运行时能按矩阵规格路由到专用路径并为其他规格保留回退"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-23",
  "evidence": [
    {
      "after_us": 662.3,
      "before_us": 829.98,
      "case": "20-case-sum-incremental",
      "operator_class": "vv-fusion",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/strategies/mhc_sinkhorn_opt_20260821.md",
      "speedup": 1.25,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "iterative-ub-roundtrip",
      "local-memory-barrier"
    ],
    "dtypes": [
      "fp32"
    ],
    "pattern": "small-matrix-register-residency",
    "reduce_mode": "iterative-normalization",
    "structure": [
      "register-resident",
      "runtime-specialization",
      "iteration-fusion"
    ]
  },
  "gain": "相对 fused-pass 829.98→662.30us，增量 1.25x；相对基线累计 3.56x，20/20 PASS。",
  "generality": "op_class",
  "id": "NORM-SMALL-MATRIX-REG",
  "implementation_steps": [
    "从矩阵尺寸和每轮临时量计算寄存器需求，确定可完整驻留的固定规格",
    "为矩阵行、列统计量和临时值声明有限个具名 RegTensor，并只在首轮从 UB 载入",
    "在一个向量函数内完成所有迭代，轮次间直接复用寄存器值，不插入不必要的 LocalMemBar",
    "最终迭代结束后一次性写回 UB/GM，其他矩阵规格运行时回退通用融合路径",
    "检查编译器寄存器分配、二进制和 profile，确认无 spill 与隐藏片上往返"
  ],
  "intent": "消除固定小矩阵在多轮归一化迭代之间反复写回和重读 UB 的开销。",
  "mechanism": "对可证明装入寄存器的小矩阵建立尺寸专用路径，将矩阵元素与统计量保存在若干具名 RegTensor 中，所有迭代在同一向量作用域完成，仅在首尾与 UB 交换数据。",
  "name": "固定小矩阵的跨迭代寄存器驻留",
  "op": "mhc_sinkhorn",
  "operator_class": "vv-fusion",
  "operator_scope": "矩阵规模很小、同一矩阵执行多轮行列归一化且轮次间无外部可见性的迭代归一化",
  "principle": "当完整工作集可装入寄存器时，每轮 UB 往返和屏障都是冗余；把全部迭代折叠进一个寄存器驻留作用域，可把片上内存交互降到首尾各一次。",
  "provenance": {
    "final_summary": "<PERF_ROOT>/strategies/mhc_sinkhorn_opt_20260821/final_summary.json",
    "source_report": "<PERF_ROOT>/strategies/mhc_sinkhorn_opt_20260821.md"
  },
  "related_anti_patterns": [],
  "risks": [
    "寄存器压力超过硬件或编译器阈值会 spill，性能可能突然恶化",
    "专用尺寸判定错误会让动态 shape 访问未定义的寄存器 lane"
  ],
  "schema_version": 2,
  "slug": "small-matrix-register-residency",
  "source": "external_verified",
  "status": "applied",
  "summary": "让固定小矩阵跨全部归一化迭代驻留 RegTensor，仅在首尾访问 UB。",
  "verification": {
    "correctness": [
      "覆盖专用尺寸与相邻非专用尺寸、不同迭代次数和极端数值，确认运行时分派及全量精度通过"
    ],
    "performance": [
      "检查 LocalMemBar 和 UB 往返消失、编译器无 spill，并比较不同 batch/迭代次数的收益边界"
    ],
    "rollback_signals": [
      "出现编译失败、寄存器 spill、尺寸误路由、精度漂移或启动开销主导形状回归时回退"
    ]
  }
}
-->

# 性能优化策略：固定小矩阵的跨迭代寄存器驻留

单一优化点：让固定小矩阵跨全部归一化迭代驻留 RegTensor，仅在首尾访问 UB。

## 1. 原理

当完整工作集可装入寄存器时，每轮 UB 往返和屏障都是冗余；把全部迭代折叠进一个寄存器驻留作用域，可把片上内存交互降到首尾各一次。

实现机制：对可证明装入寄存器的小矩阵建立尺寸专用路径，将矩阵元素与统计量保存在若干具名 RegTensor 中，所有迭代在同一向量作用域完成，仅在首尾与 UB 交换数据。

## 2. 性能问题模式

- 优化目标：消除固定小矩阵在多轮归一化迭代之间反复写回和重读 UB 的开销。
- 适用数据流：矩阵规模很小、同一矩阵执行多轮行列归一化且轮次间无外部可见性的迭代归一化
- Feature signature：`{"bottleneck": ["iterative-ub-roundtrip", "local-memory-barrier"], "dtypes": ["fp32"], "pattern": "small-matrix-register-residency", "reduce_mode": "iterative-normalization", "structure": ["register-resident", "runtime-specialization", "iteration-fusion"]}`

## 3. 正确性红线

- 寄存器压力超过硬件或编译器阈值会 spill，性能可能突然恶化
- 专用尺寸判定错误会让动态 shape 访问未定义的寄存器 lane

资源与硬件约束：

- 必须使用编译器可接受的具名 RegTensor，禁止依赖不支持的 RegTensor 数组
- 寄存器预算需覆盖矩阵、行列统计量和临时值，并用编译结果确认没有 spill

## 4. 泛化条件

- 策略作用域：op_class：vv-fusion

适用：

- 单个小矩阵及迭代所需统计量可完整驻留向量寄存器
- 归一化迭代只在该矩阵内部读写，轮次间无需对外可见
- 运行时能按矩阵规格路由到专用路径并为其他规格保留回退

不适用：

- 矩阵尺寸动态且超过寄存器预算、迭代逻辑含跨核依赖或编译器产生 spill 时不适用
- 迭代次数很少或 batch 很小、kernel 启动成本占主导时收益有限

## 5. 实施步骤

1. 从矩阵尺寸和每轮临时量计算寄存器需求，确定可完整驻留的固定规格
2. 为矩阵行、列统计量和临时值声明有限个具名 RegTensor，并只在首轮从 UB 载入
3. 在一个向量函数内完成所有迭代，轮次间直接复用寄存器值，不插入不必要的 LocalMemBar
4. 最终迭代结束后一次性写回 UB/GM，其他矩阵规格运行时回退通用融合路径
5. 检查编译器寄存器分配、二进制和 profile，确认无 spill 与隐藏片上往返

## 6. LLM 前置问题

- 目标实现是否满足：单个小矩阵及迭代所需统计量可完整驻留向量寄存器？
- 目标实现是否满足：归一化迭代只在该矩阵内部读写，轮次间无需对外可见？
- 目标实现是否满足：运行时能按矩阵规格路由到专用路径并为其他规格保留回退？
- 是否命中排除条件：矩阵尺寸动态且超过寄存器预算、迭代逻辑含跨核依赖或编译器产生 spill 时不适用？

## 7. 验收标准

正确性：

- 覆盖专用尺寸与相邻非专用尺寸、不同迭代次数和极端数值，确认运行时分派及全量精度通过

性能：

- 检查 LocalMemBar 和 UB 往返消失、编译器无 spill，并比较不同 batch/迭代次数的收益边界

回滚信号：

- 出现编译失败、寄存器 spill、尺寸误路由、精度漂移或启动开销主导形状回归时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- strategy-mhc-sinkhorn-20260821-s2（status=accepted, case=20-case-sum-incremental, speedup=1.25）

## 检索卡（短卡）

动作：把多轮归一化折叠进单个寄存器驻留作用域，将每轮 UB 往返改为首尾各一次。
适用：小矩阵及统计量可完整驻留向量寄存器，且迭代轮次间无需对外可见。
限制：必须使用编译器接受的具名 RegTensor，不得依赖不支持的 RegTensor 数组。
范围：normalization 中固定小矩阵的多轮行列归一化。
检索词：RegTensor、寄存器驻留、UB 往返、行列统计量、迭代归一化。
机会：固定小矩阵在多轮归一化之间反复写回、重读 UB。
代价：寄存器压力越过硬件或编译器阈值会 spill。
