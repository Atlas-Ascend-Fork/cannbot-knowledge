---
type: Optimization
title: 利用保序键空余位合并值与关联位置扫描
description: 把独立维护的值键和局部位置编码为一个整数状态，用一次 Min 完成联合选择。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/spare-key-bits-associated-index-scan.md
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
      "完整精度键无空余位",
      "位置超出编码容量"
    ],
    "required_conditions": [
      "删去键低b位仍保持全部合法值的顺序与必要相等关系",
      "局部块长M<=2^b",
      "整数比较方向与编码一致"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "duplicated-scan-state-selection"
    ],
    "pattern": "packed-value-position-state",
    "structure": [
      "ordered-key",
      "spare-low-bits",
      "prefix-state"
    ]
  },
  "generality": "pattern",
  "id": "SPARE-KEY-BITS-ASSOCIATED-INDEX-SCAN",
  "implementation_steps": [
    "定义值键与特殊值规则，确定可占用位数 b；检查编码前后的全序。",
    "选 M<=2^b，清低 b 位后写入局部位置优先级，保持载体比较类型一致。",
    "用单状态整数最值替换扫描树中的双状态选择，保留有效 lane 掩码。",
    "解出获胜位置，叠加块基址并 Gather 原值；块间独立处理 carry 的全局 tie-break。"
  ],
  "intent": "前缀最值及关联位置扫描的每层树分别 Gather 值与索引，再执行比较、相等判断和 Select。",
  "mechanism": "把不改变值序的空余低位分配给局部位置优先级，使一次整数最值同时选择值与位置。",
  "name": "利用保序键空余位合并值与关联位置扫描",
  "operator_scope": "有空余低位的保序键、M<=2^b、需要同步选择值与关联位置的前缀或局部归约。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "若输入可无损提升到较宽格式，其保序键可能含有不承载有效信息的低位。设清除低 b 位不合并不同合法值，局部块长为 M，同值取后位置时，将键的低 b 位写成 M-1-i。整数 Min 便先比较值，再在相同值中选较大的局部位置。FP16/BF16 无损提升到 FP32 后可检查这一性质；不能直接截断任意 FP32 键。该机制合并的是比较状态，与把相邻输入元素打包为同一访存字互相独立。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "必须证明删位后的严格值序、同值关系与有符号/无符号比较解释一致，不能仅检查随机输入",
    "NaN 优先级、相同 NaN 的位置选择及 ±0 合键规则先按契约编码",
    "值输出应按获胜位置读取原始位型，不能从被覆盖低位的键重建",
    "局部位置不能冒充全局位置；跨块 carry 保留完整全局位置，并按相同值的先后契约与当前块合并",
    "无效 lane 不得赢过有效数据"
  ],
  "schema_version": 2,
  "slug": "spare-key-bits-associated-index-scan",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "把独立维护的值键和局部位置编码为一个整数状态，用一次 Min 完成联合选择。",
  "verification": {
    "correctness": [
      "对有限窄编码域检查键序、不同值碰撞与局部索引编码，覆盖跨块同值胜者、NaN 连续出现及尾块"
    ],
    "performance": [
      "编译结果应减少双状态 Gather/Select 链；比较完整扫描耗时，若编解码或 carry 合并抵消收益则退回双状态表示"
    ],
    "rollback_signals": [
      "键压缩会合并不同值、载体溢出、tie-break 不能表示为局部优先级，或跨块状态无法恢复完整索引"
    ]
  }
}
-->

# 性能优化策略：利用保序键空余位合并值与关联位置扫描

单一优化点：把独立维护的值键和局部位置编码为一个整数状态，用一次 Min 完成联合选择。

## 1. 原理

若输入可无损提升到较宽格式，其保序键可能含有不承载有效信息的低位。设清除低 b 位不合并不同合法值，局部块长为 M，同值取后位置时，将键的低 b 位写成 M-1-i。整数 Min 便先比较值，再在相同值中选较大的局部位置。FP16/BF16 无损提升到 FP32 后可检查这一性质；不能直接截断任意 FP32 键。该机制合并的是比较状态，与把相邻输入元素打包为同一访存字互相独立。

## 2. 性能问题模式

前缀最值及关联位置扫描的每层树分别 Gather 值与索引，再执行比较、相等判断和 Select。索引选择链与值选择链重复搬移相同胜者状态，增加向量指令和活跃寄存器。联合整数状态只在入口编码、出口解码。

## 3. 正确性红线

必须证明删位后的严格值序、同值关系与有符号/无符号比较解释一致，不能仅检查随机输入。NaN 优先级、相同 NaN 的位置选择及 ±0 合键规则先按契约编码。值输出应按获胜位置读取原始位型，不能从被覆盖低位的键重建。局部位置不能冒充全局位置；跨块 carry 保留完整全局位置，并按相同值的先后契约与当前块合并。无效 lane 不得赢过有效数据。

## 4. 泛化条件

适用：有空余低位的保序键、M<=2^b、需要同步选择值与关联位置的前缀或局部归约。

不适用：键压缩会合并不同值、载体溢出、tie-break 不能表示为局部优先级，或跨块状态无法恢复完整索引。

## 5. 实施步骤

1. 定义值键与特殊值规则，确定可占用位数 b；检查编码前后的全序。
2. 选 M<=2^b，清低 b 位后写入局部位置优先级，保持载体比较类型一致。
3. 用单状态整数最值替换扫描树中的双状态选择，保留有效 lane 掩码。
4. 解出获胜位置，叠加块基址并 Gather 原值；块间独立处理 carry 的全局 tie-break。

## 6. LLM 前置问题

- 可占用低位是由 dtype 保证，还是仅因当前数据恰好相同？
- NaN、零和跨块等值胜者是否共享明确的全序契约？
- 编解码成本能否由扫描层数中的指令节省摊销？

## 7. 验收标准

对有限窄编码域检查键序、不同值碰撞与局部索引编码，覆盖跨块同值胜者、NaN 连续出现及尾块。编译结果应减少双状态 Gather/Select 链；比较完整扫描耗时，若编解码或 carry 合并抵消收益则退回双状态表示。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：把保序键空余低位写入局部位置优先级，以一次整数Min联合扫描值与位置。
适用：删去低b位仍保持合法值顺序与必要相等关系；局部块长M<=2^b；比较类型一致。
限制：完整精度键不可任意截断；NaN与零按契约编码；跨块保留完整全局索引；按获胜位置读取原值位型。
范围：前缀最值及关联位置扫描、局部归约。
检索词：ordered key、Min、Gather、tie-break、carry、空余低位
机会：扫描树每层分别Gather和Select值与索引，重复搬移胜者状态。
代价：入口编码、出口解码与跨块carry合并；需证明全序和位置容量。
