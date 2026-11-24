---
type: Optimization
title: 完整窄浮点编码域占用表替代输入排序
description: 使用完整窄类型编码域记录占用和代表，以固定域扫描代替全输入排序。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/full-narrow-float-code-occupancy.md
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
      "未经证明的NaN规则",
      "更宽类型直接按全域展开"
    ],
    "required_conditions": [
      "FP16/BF16且原契约无NaN",
      "65536槽域表及扫描成本可接受",
      "零代表与原始位型语义明确"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "full-input-sort",
      "finite-type-domain"
    ],
    "pattern": "full-narrow-float-code-occupancy"
  },
  "generality": "pattern",
  "id": "full-narrow-float-code-occupancy",
  "implementation_steps": [
    "定义全域保序编码及零键规则，预算占用、代表、rank 和扫描缓冲。",
    "初始化域表，读取输入原始位型，安全记录占用和代表。",
    "对占用位做域前缀，按 rank 复制原值代表并生成键到 rank 映射。",
    "再遍历输入恢复原位置编号；保留通用排序回退并比较全调用。"
  ],
  "intent": "基线因浮点含小数而走通用排序，多轮比较或分发反复搬运全部输入。",
  "mechanism": "以完整16位浮点保序编码域建立占用和代表表，扫描域生成有序值及rank映射。",
  "name": "完整窄浮点编码域占用表替代输入排序",
  "operator_scope": "FP16/BF16 无 NaN 输入的精确值去重、值压缩或有序编号，完整 65536 槽表和扫描成本可接受，原值与代表语义明确。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "FP16/BF16 各只有 65536 种位模式，可由原始 uint16 编码构造精确保序键：负值编码按位反转，非负编码翻转符号位，并按契约统一零键。每个输入仅标记对应槽位并保存原值代表；扫描占用表的前缀得到有序 rank，再按 rank 输出代表，并通过键到 rank 表生成原位置映射。该机制覆盖合法小数与非正规数，无需先证明浮点值为整数；避免对 N 个输入执行完整排序。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "位编码只用于比较和寻址，输出从输入代表按原始位型复制，不以浮点运算重建值，避免非正规数刷新或符号位丢失",
    "±0 是否合并按原契约决定；合并且要求最早零代表时，必须维护最早原始索引，不能任取已占用代表",
    "NaN 的等价、排序及 payload 规则需要另证，本子模式以原契约无 NaN 为前提，不能宣称所有浮点位模式均已支持",
    "表的空哨兵、索引及计数宽度须容纳输入上界；仅占用槽产生有效 rank，不得解引用或输出未占用槽的代表值",
    "分阶段扫描及输出按同流顺序完成，实际跨步地址须独立于逻辑键计算"
  ],
  "schema_version": 2,
  "slug": "full-narrow-float-code-occupancy",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "使用完整窄类型编码域记录占用和代表，以固定域扫描代替全输入排序。",
  "verification": {
    "correctness": [
      "覆盖正负值、分数、非正规数、极值、双符号零和重复代表，核对值序、原始位型及位置映射"
    ],
    "performance": [
      "计入表初始化、全部扫描与启动，对小输入和低重复率确认回退边界"
    ],
    "rollback_signals": [
      "NaN 规则未证、更宽类型直接全域展开，或固定域成本超过输入排序",
      "不得依公开样例的窄值域缩表；若缩域必须独立证明实际范围和编码无碰撞"
    ]
  }
}
-->

# 性能优化策略：完整窄浮点编码域占用表替代输入排序

单一优化点：使用完整窄类型编码域记录占用和代表，以固定域扫描代替全输入排序。

## 1. 原理

FP16/BF16 各只有 65536 种位模式，可由原始 uint16 编码构造精确保序键：负值编码按位反转，非负编码翻转符号位，并按契约统一零键。每个输入仅标记对应槽位并保存原值代表；扫描占用表的前缀得到有序 rank，再按 rank 输出代表，并通过键到 rank 表生成原位置映射。该机制覆盖合法小数与非正规数，无需先证明浮点值为整数；避免对 N 个输入执行完整排序。

## 2. 性能问题模式

基线因浮点含小数而走通用排序，多轮比较或分发反复搬运全部输入。完整类型域将主要工作转为 O(N+D)，D=65536，与输入数值分布的范围无关。代价是域表初始化、占用 CAS、代表及 rank 空间、固定全域扫描和阶段启动；小输入或低重复率未必获益。

## 3. 正确性红线

位编码只用于比较和寻址，输出从输入代表按原始位型复制，不以浮点运算重建值，避免非正规数刷新或符号位丢失。±0 是否合并按原契约决定；合并且要求最早零代表时，必须维护最早原始索引，不能任取已占用代表。NaN 的等价、排序及 payload 规则需要另证，本子模式以原契约无 NaN 为前提，不能宣称所有浮点位模式均已支持。

表的空哨兵、索引及计数宽度须容纳输入上界；仅占用槽产生有效 rank，不得解引用或输出未占用槽的代表值。分阶段扫描及输出按同流顺序完成，实际跨步地址须独立于逻辑键计算。

## 4. 泛化条件

适用：FP16/BF16 无 NaN 输入的精确值去重、值压缩或有序编号，完整 65536 槽表和扫描成本可接受，原值与代表语义明确。

不适用或需退回：NaN 规则未证、更宽类型直接全域展开，或固定域成本超过输入排序。不得依公开样例的窄值域缩表；若缩域必须独立证明实际范围和编码无碰撞。

## 5. 实施步骤

1. 定义全域保序编码及零键规则，预算占用、代表、rank 和扫描缓冲。
2. 初始化域表，读取输入原始位型，安全记录占用和代表。
3. 对占用位做域前缀，按 rank 复制原值代表并生成键到 rank 映射。
4. 再遍历输入恢复原位置编号；保留通用排序回退并比较全调用。

## 6. LLM 前置问题

类型域是否足够小？NaN 是否在原契约之外？零如何选代表？非正规数能否全程位复制？固定域扫描会否大于排序成本？

## 7. 验收标准

覆盖正负值、分数、非正规数、极值、双符号零和重复代表，核对值序、原始位型及位置映射。计入表初始化、全部扫描与启动，对小输入和低重复率确认回退边界。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：将窄浮点原始编码映射完整保序域，记录占用和代表，经域前缀生成有序rank及位置映射。
适用：FP16/BF16且原契约无NaN；65536槽表和扫描成本可接受。
限制：原值位复制保留非正规数；±0按契约合键并维护最早零代表；NaN另证；索引计数不溢出。
范围：窄浮点精确值去重、值压缩及有序编号。
检索词：FP16、BF16、65536、occupancy、rank table、raw bits
机会：含小数的窄浮点仍走全输入排序，重复搬运全部输入。
代价：固定域初始化、占用CAS、代表表及全域扫描；小输入未必获益。
