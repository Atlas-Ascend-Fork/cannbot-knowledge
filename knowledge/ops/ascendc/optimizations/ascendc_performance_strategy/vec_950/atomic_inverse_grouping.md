---
type: Optimization
title: 允许重排的线性原子逆向分组
description: 把每组扫描全部输入的成员查找，改为每输入一次原子挂链并跨特征复用。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.atomic
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/atomic-inverse-grouping.md
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
      "要求稳定输入顺序或逐位固定浮点累加次序"
    ],
    "required_conditions": [
      "组ID有效，每输入独占一个next项",
      "允许组内遍历次序变化",
      "构建结束后再消费"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "repeated-membership-scan",
      "group-map-construction"
    ],
    "pattern": "atomic-inverse-grouping"
  },
  "generality": "pattern",
  "id": "atomic-inverse-grouping",
  "implementation_steps": [
    "检查顺序契约，确定索引宽度、空哨兵和 workspace 容量。",
    "初始化全部 head，独立建链阶段为每输入执行 atomic exchange 并写 next。",
    "在同流完成边界后启动消费者，每个输出位置独占写回，复用链遍历特征列。",
    "按输入规模、特征宽度和组分布评估全调用门控。"
  ],
  "intent": "基线为每组反复扫描全部 ID，再累加对应特征，成员筛选占用大量标量比较及 GM 读取；特征越多，分组预处理越易摊薄。",
  "mechanism": "每个输入项以一次atomic exchange挂接逆向链，构建后由多个特征列复用分组。",
  "name": "允许重排的线性原子逆向分组",
  "operator_scope": "按离散 ID 分组且多个特征可共享成员关系；N+S 个索引槽可容纳，构建及链遍历成本能小于重复扫描。浮点误差需在原容差下验证，不以交换律推定逐位等价。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "设 N 个输入归入 S 个组，每个输入还带多个特征列。为每组初始化 head 为空，对输入 i 执行 old=atomic exchange(head[group[i]],i)，再写 next[i]=old。每输入独占 next[i]，链头更新由原子操作串行化，得到每组的逆向成员链。初始化和建链总工作量为 O(N+S)，后续各特征列复用链，避免 O(N*S) 的重复成员判断。链序由并发执行决定，并非原输入顺序。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "必须允许归约重排；稳定输出代表、顺序敏感计算及要求固定浮点累加次序的契约不能使用",
    "ID 必须落在 [0,S)，每输入恰好加入一次，next 地址和哨兵不能与合法索引重叠",
    "消费者必须等整个建链阶段完成，不能看到已发布 head 而未写好的 next；不得用无跨核进度保证的自旋代替阶段边界",
    "空组输出中性元，累加类型、整数溢出语义及最终转换均保持原契约"
  ],
  "schema_version": 2,
  "slug": "atomic-inverse-grouping",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "把每组扫描全部输入的成员查找，改为每输入一次原子挂链并跨特征复用。",
  "verification": {
    "correctness": [
      "覆盖空组、单组热点、重复 ID、非连续布局与索引宽度边界；检查每输入只归入一组且链无环、无丢失"
    ],
    "performance": [
      "核对浮点误差及完整调用，初始化、建链和消费耗时均计入"
    ],
    "rollback_signals": [
      "输入很小、特征很窄、极端热点使原子竞争主导，或必须维护输入先后次序",
      "保留直接扫描或稳定建组路径"
    ]
  }
}
-->

# 性能优化策略：允许重排的线性原子逆向分组

单一优化点：把每组扫描全部输入的成员查找，改为每输入一次原子挂链并跨特征复用。

## 1. 原理

设 N 个输入归入 S 个组，每个输入还带多个特征列。为每组初始化 head 为空，对输入 i 执行 old=atomic exchange(head[group[i]],i)，再写 next[i]=old。每输入独占 next[i]，链头更新由原子操作串行化，得到每组的逆向成员链。初始化和建链总工作量为 O(N+S)，后续各特征列复用链，避免 O(N*S) 的重复成员判断。链序由并发执行决定，并非原输入顺序。

## 2. 性能问题模式

基线为每组反复扫描全部 ID，再累加对应特征，成员筛选占用大量标量比较及 GM 读取；特征越多，分组预处理越易摊薄。该方法引入初始化启动、head/next 空间、原子竞争和链式间接读取，热点组可能串行化。

## 3. 正确性红线

必须允许归约重排；稳定输出代表、顺序敏感计算及要求固定浮点累加次序的契约不能使用。ID 必须落在 [0,S)，每输入恰好加入一次，next 地址和哨兵不能与合法索引重叠。消费者必须等整个建链阶段完成，不能看到已发布 head 而未写好的 next；不得用无跨核进度保证的自旋代替阶段边界。空组输出中性元，累加类型、整数溢出语义及最终转换均保持原契约。

## 4. 泛化条件

适用：按离散 ID 分组且多个特征可共享成员关系；N+S 个索引槽可容纳，构建及链遍历成本能小于重复扫描。浮点误差需在原容差下验证，不以交换律推定逐位等价。

不适用或需退回：输入很小、特征很窄、极端热点使原子竞争主导，或必须维护输入先后次序。保留直接扫描或稳定建组路径。

## 5. 实施步骤

1. 检查顺序契约，确定索引宽度、空哨兵和 workspace 容量。
2. 初始化全部 head，独立建链阶段为每输入执行 atomic exchange 并写 next。
3. 在同流完成边界后启动消费者，每个输出位置独占写回，复用链遍历特征列。
4. 按输入规模、特征宽度和组分布评估全调用门控。

## 6. LLM 前置问题

是否必须保序？ID 是否已证明合法？索引是否可能越过哨兵？如何保证 next 全部完成后消费？热点竞争能否抵消复杂度下降？

## 7. 验收标准

覆盖空组、单组热点、重复 ID、非连续布局与索引宽度边界；检查每输入只归入一组且链无环、无丢失。核对浮点误差及完整调用，初始化、建链和消费耗时均计入。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：初始化组head，每输入一次atomic exchange挂入head/next逆向链，供多个特征列复用。
适用：有效组ID、每输入独占next；允许归约重排；N+S个索引槽可容纳。
限制：稳定输入顺序或固定浮点累加次序不可用；等整个建链完成再消费；哨兵不与合法索引重叠。
范围：按离散ID分组的成员预处理及多特征归约。
检索词：atomic exchange、inverse grouping、head/next、O(N+S)、GM
机会：每组重复扫描全部ID，成员构建开销O(N*S)。
代价：初始化启动、索引空间、热点原子竞争及链式间接读取。
