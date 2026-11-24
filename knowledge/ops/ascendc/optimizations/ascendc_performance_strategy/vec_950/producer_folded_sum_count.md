---
type: Optimization
title: 生产阶段折叠有效值之和与计数
description: 把归约的第一级累计并入原生产循环，删除逐项结果与有效标记的 GM 物化。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/producer-folded-sum-count.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "excluded_conditions": [
      "需要逐项输出或中间数组有其他消费者"
    ],
    "required_conditions": [
      "逐项值和有效标记只被最终归约消费",
      "统计状态能跨生产tile保持"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "single-consumer-materialization",
      "redundant-partial-kernel"
    ],
    "pattern": "producer-folded-sum-count"
  },
  "generality": "pattern",
  "id": "producer-folded-sum-count",
  "implementation_steps": [
    "沿数据流确认中间数组的全部消费者和有效性定义。",
    "为每线程或向量 lane 初始化 sum/count，生产有效项时就地累计。",
    "tile 循环结束后核内合并，写每核 partial，删除独立扫描及中间分配。",
    "最终按原空组和类型转换规则合并，比较完整调用并设置资源回退。"
  ],
  "intent": "数据流为生产逐项值、写有效标记、独立扫描求 partial、最后汇总；中间数组没有其他消费者，MTE 流量及额外 launch 占比高。",
  "mechanism": "在原生产循环中累计sum/count，仅写每核partial，删除逐项中间数组和独立扫描阶段。",
  "name": "生产阶段折叠有效值之和与计数",
  "operator_scope": "最终目标仅是 sum 或 mean，逐项值及标记没有外部可见用途；生产循环可以维护有界统计状态，原误差契约允许新的合并次序。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "若生产者生成的每项结果及有效标记只供最终求和或求均值使用，就不必先写完整数组，再启动独立阶段扫描生成 partial。生产每项时同步累计有效值之和及有效计数，核内合并后仅写每核 sum/count。中间空间从与输入长度成比例缩为与核数成比例，并删掉一次完整数组读写和一次扫描启动；跨核最终合并仍需保留。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "有效性判断必须保留完整索引或标签宽度，不得先截断再比较忽略标记",
    "无效项既不能计入和，也不能计入计数；掩码之外的旧值不得参与归约",
    "均值分母为真实有效数，空组、全部忽略以及零分母语义按原契约处理",
    "计数宽度必须容纳全部输入；若宽度未证明可缩小，保留 uint64",
    "累加器跨全部生产 tile 存活，空核也输出中性元，不在循环尾意外重置"
  ],
  "schema_version": 2,
  "slug": "producer-folded-sum-count",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "把归约的第一级累计并入原生产循环，删除逐项结果与有效标记的 GM 物化。",
  "verification": {
    "correctness": [
      "覆盖全有效、全忽略、混合有效、空核、尾 tile 和计数边界"
    ],
    "performance": [
      "核对特殊值与输出舍入，确认删除的分配及启动确实不再发生；完整路径收益需覆盖资源占用增加和最终合并成本"
    ],
    "rollback_signals": [
      "需要逐项输出、其他消费者依赖中间数组，或融合后资源占用降低并行度",
      "原任务被分拆时须重新证明每项只累计一次，不能直接把多个生产分片都计入 count"
    ]
  }
}
-->

# 性能优化策略：生产阶段折叠有效值之和与计数

单一优化点：把归约的第一级累计并入原生产循环，删除逐项结果与有效标记的 GM 物化。

## 1. 原理

若生产者生成的每项结果及有效标记只供最终求和或求均值使用，就不必先写完整数组，再启动独立阶段扫描生成 partial。生产每项时同步累计有效值之和及有效计数，核内合并后仅写每核 sum/count。中间空间从与输入长度成比例缩为与核数成比例，并删掉一次完整数组读写和一次扫描启动；跨核最终合并仍需保留。

## 2. 性能问题模式

数据流为生产逐项值、写有效标记、独立扫描求 partial、最后汇总；中间数组没有其他消费者，MTE 流量及额外 launch 占比高。融合会延长累加器生命周期，增加 UB 或寄存器占用、核内同步及最终局部合并成本，也可能改变浮点归约顺序。

## 3. 正确性红线

有效性判断必须保留完整索引或标签宽度，不得先截断再比较忽略标记。无效项既不能计入和，也不能计入计数；掩码之外的旧值不得参与归约。均值分母为真实有效数，空组、全部忽略以及零分母语义按原契约处理。计数宽度必须容纳全部输入；若宽度未证明可缩小，保留 uint64。累加器跨全部生产 tile 存活，空核也输出中性元，不在循环尾意外重置。

## 4. 泛化条件

适用：最终目标仅是 sum 或 mean，逐项值及标记没有外部可见用途；生产循环可以维护有界统计状态，原误差契约允许新的合并次序。

不适用或需退回：需要逐项输出、其他消费者依赖中间数组，或融合后资源占用降低并行度。原任务被分拆时须重新证明每项只累计一次，不能直接把多个生产分片都计入 count。

## 5. 实施步骤

1. 沿数据流确认中间数组的全部消费者和有效性定义。
2. 为每线程或向量 lane 初始化 sum/count，生产有效项时就地累计。
3. tile 循环结束后核内合并，写每核 partial，删除独立扫描及中间分配。
4. 最终按原空组和类型转换规则合并，比较完整调用并设置资源回退。

## 6. LLM 前置问题

中间结果是否真的只有归约消费者？有效标记何时产生？计数会否溢出？跨 tile 与分片是否恰好覆盖一次？融合会增加多少活跃状态？

## 7. 验收标准

覆盖全有效、全忽略、混合有效、空核、尾 tile 和计数边界。核对特殊值与输出舍入，确认删除的分配及启动确实不再发生；完整路径收益需覆盖资源占用增加和最终合并成本。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：生产每项结果时直接累计sum/count，只写每核partial，删除逐项数组及独立扫描。
适用：最终仅sum或mean；中间值及标记无其他消费者；状态可跨tile保持。
限制：完整宽度判断忽略项；空组及全忽略语义不变；计数不得溢出；每项只累计一次。
范围：带有效性筛选的生产与最终归约之间。
检索词：producer partial、sum/count、materialization、uint64、tile
机会：逐项值和标记落GM后又被独立kernel全量读取归约。
代价：延长累加器寿命、增加资源及核内同步；仍需最终合并。
