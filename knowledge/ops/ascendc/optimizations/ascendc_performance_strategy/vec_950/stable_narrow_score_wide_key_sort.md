---
type: Optimization
title: 以稳定窄分数原生排序合成精确宽键顺序
description: 把完整宽键比较桥接为若干次精确窄分数的原生排序，保持索引载荷及原始值位型。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/stable-narrow-score-wide-key-sort.md
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
      "任一归并层破坏同分输入次序",
      "用窄分数重建原始值"
    ],
    "required_conditions": [
      "原生分数能精确编码每个窄位段",
      "Sort32与所有MrgSort层同分稳定",
      "载荷及缓冲容量合法"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "wide-key-comparison",
      "scalar-key-ordering"
    ],
    "pattern": "stable-narrow-native-sort-bridge",
    "structure": [
      "ordered-32-bit-key",
      "16-bit-digits",
      "Sort32",
      "MrgSort",
      "original-bit-Gather"
    ]
  },
  "generality": "pattern",
  "id": "STABLE-NARROW-SCORE-WIDE-KEY-SORT",
  "implementation_steps": [
    "定义特殊值保序键与同值载荷次序，保存每项原始索引。",
    "为窄位段构造正常 float 的精确单调编码，确认升降方向与排序接口一致。",
    "低位轮执行块内排序和稳定归并，载荷传播原始索引。",
    "按上一轮载荷取高位数字，保持输入顺序，执行同方向稳定排序及归并。",
    "按最终索引 Gather 原值位型，筛除 padding 并写出有效项。"
  ],
  "intent": "宽浮点值的直接分数排序难以保留完整键序，改用通用宽键比较或标量筛选又消耗较多控制和比较指令。",
  "mechanism": "将宽保序键拆为可精确表示的窄分数，低位到高位稳定原生排序，最后按索引读取原值位型。",
  "name": "以稳定窄分数原生排序合成精确宽键顺序",
  "operator_scope": "可构造完整保序键、每个窄位段能被原生分数精确编码、全部 Sort32/MrgSort 层同分稳定，且索引与 ping-pong 缓冲满足 UB 预算。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "当原生排序对 float 分数高效，却难以直接表达完整宽整数键时，可把 32 位保序键拆成低 16 位和高 16 位。每个 16 位数字编码为互异、单调且精确可表示的正常 float 分数：例如固定指数、把数字放入尾数低位，避免非正规分数被清零。先稳定排序低位，再按高位稳定排序，便得到完整键的字典序；Sort32 块内排序与各级 MrgSort 都必须保持同分输入次序。该策略专门连接宽键语义与窄分数原生接口，最终值由索引 Gather 原始位型。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "高位轮必须沿用低位轮产出的输入顺序，任一块内或跨块归并层不稳定都会破坏宽键排序",
    "按降序处理时，两轮方向须一致，不能在最后简单翻转数组而破坏同值稳定性",
    "NaN 优先级与 ±0 合键规则先写入保序键，同值位置规则由稳定载荷次序保证；即使键规范化，输出仍读取原始值位型",
    "padding 必须严格排在有效项外，并保留有效索引范围；不能将分数转换结果作为原值输出"
  ],
  "schema_version": 2,
  "slug": "stable-narrow-score-wide-key-sort",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "把完整宽键比较桥接为若干次精确窄分数的原生排序，保持索引载荷及原始值位型。",
  "verification": {
    "correctness": [
      "构造同高位异低位、跨原生块及跨归并边界的同分输入，检查完整键序和原始位型；覆盖 NaN、零、非正规数及尾 padding"
    ],
    "performance": [
      "确认原生路径实际执行，按所有 pass、Gather 与缓冲搬运计时；若多轮排序或 UB 压力占优，则回退通用宽键路径"
    ],
    "rollback_signals": [
      "稳定性无保证、分数位型被硬件规范化、载荷无法保持原索引，或多轮代价高于原有宽键路径",
      "长度阈值应按缓冲容量与完整调用代价设定"
    ]
  }
}
-->

# 性能优化策略：以稳定窄分数原生排序合成精确宽键顺序

单一优化点：把完整宽键比较桥接为若干次精确窄分数的原生排序，保持索引载荷及原始值位型。

## 1. 原理

当原生排序对 float 分数高效，却难以直接表达完整宽整数键时，可把 32 位保序键拆成低 16 位和高 16 位。每个 16 位数字编码为互异、单调且精确可表示的正常 float 分数：例如固定指数、把数字放入尾数低位，避免非正规分数被清零。先稳定排序低位，再按高位稳定排序，便得到完整键的字典序；Sort32 块内排序与各级 MrgSort 都必须保持同分输入次序。该策略专门连接宽键语义与窄分数原生接口，最终值由索引 Gather 原始位型。

## 2. 性能问题模式

宽浮点值的直接分数排序难以保留完整键序，改用通用宽键比较或标量筛选又消耗较多控制和比较指令。数据可驻片上而原生排序通路闲置时，可用少量窄分数 pass 替换宽键软件工作。代价是多轮排序、索引载荷与中间缓冲，并非总比单轮原生分数排序快。

## 3. 正确性红线

高位轮必须沿用低位轮产出的输入顺序，任一块内或跨块归并层不稳定都会破坏宽键排序。按降序处理时，两轮方向须一致，不能在最后简单翻转数组而破坏同值稳定性。NaN 优先级与 ±0 合键规则先写入保序键，同值位置规则由稳定载荷次序保证；即使键规范化，输出仍读取原始值位型。padding 必须严格排在有效项外，并保留有效索引范围；不能将分数转换结果作为原值输出。

## 4. 泛化条件

适用：可构造完整保序键、每个窄位段能被原生分数精确编码、全部 Sort32/MrgSort 层同分稳定，且索引与 ping-pong 缓冲满足 UB 预算。

不适用：稳定性无保证、分数位型被硬件规范化、载荷无法保持原索引，或多轮代价高于原有宽键路径。长度阈值应按缓冲容量与完整调用代价设定。

## 5. 实施步骤

1. 定义特殊值保序键与同值载荷次序，保存每项原始索引。
2. 为窄位段构造正常 float 的精确单调编码，确认升降方向与排序接口一致。
3. 低位轮执行块内排序和稳定归并，载荷传播原始索引。
4. 按上一轮载荷取高位数字，保持输入顺序，执行同方向稳定排序及归并。
5. 按最终索引 Gather 原值位型，筛除 padding 并写出有效项。

## 6. LLM 前置问题

- 同分稳定性覆盖了所有归并层，还是只检查了一个 Sort32 块？
- 数字到正常 float 的映射是否无碰撞且不经过有损转换？
- 两轮所有分数、索引及暂存缓冲是否能同时容纳？

## 7. 验收标准

构造同高位异低位、跨原生块及跨归并边界的同分输入，检查完整键序和原始位型；覆盖 NaN、零、非正规数及尾 padding。确认原生路径实际执行，按所有 pass、Gather 与缓冲搬运计时；若多轮排序或 UB 压力占优，则回退通用宽键路径。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：把32位保序键拆低16/高16位，依次稳定原生排序，最后按索引Gather原始值位型。
适用：窄数字可精确编码为正常float分数；Sort32及全部MrgSort层同分稳定；缓冲预算合法。
限制：高位轮沿用低位轮次序；方向一致；NaN/零按契约成键；padding不得获胜；分数不可重建原值。
范围：宽键顺序接入窄分数原生排序接口。
检索词：Sort32、MrgSort、stable sort、16-bit score、Gather、ordered key
机会：完整宽键难以直接作为原生分数，软件宽键比较或标量筛选成本高。
代价：多轮排序、索引载荷与中间缓冲；UB压力可能抵消原生排序收益。
