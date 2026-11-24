---
type: Optimization
title: 有界幂二缩放后使用原生除法
description: 用受限幂二缩放修复特定 FTZ 敏感区间，从而以原生 Div 替代高代价精确除法。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/bounded-power-two-native-division.md
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
      "要求任意次正规数全IEEE等价",
      "范围无界或缩放溢出",
      "最终恢复仍违反FTZ契约"
    ],
    "required_conditions": [
      "已知分子分母和中间商的合法范围",
      "存在安全整数缩放指数",
      "最终误差与特殊值契约允许原生除法"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "expensive-no-FTZ-division",
      "precision-helper-stack"
    ],
    "pattern": "bounded-scaled-native-divide",
    "structure": [
      "range-proof",
      "power-of-two-scaling",
      "native-Div"
    ]
  },
  "generality": "pattern",
  "id": "BOUNDED-POWER-TWO-NATIVE-DIVISION",
  "implementation_steps": [
    "标出 FTZ 发生在输入、除法中间量还是结果，写出全部上下界。",
    "推导安全 k 的交集，选择分子上移后恢复或分子分母同移，不把固定 k 当通用常量。",
    "保留零值及特殊值分支，在满足范围条件的路径启用 native Div。",
    "独立检查缩放、Div、恢复和最终转换的误差传播，并核对生成的辅助调用与栈变化。"
  ],
  "intent": "热点除法为保留极小输入而使用精确辅助路径，带来较长指令链、寄存器或线程栈开销；实际合法数据域远窄于全浮点域。",
  "mechanism": "以可证明安全的幂二缩放迁移FTZ敏感除法的中间值范围，再用原生Div替代昂贵精确模式。",
  "name": "有界幂二缩放后使用原生除法",
  "operator_scope": "存在可证明的分子分母范围、安全整数缩放指数 k，以及允许原生除法误差的最终输出契约；精确除法是计算热点。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "当除法的少量合法输入落入 FTZ 敏感段，整条向量链可能被迫采用支持次正规数的昂贵模式。若能证明输入及中间值范围，可选整数 k，把数值迁移到原生 Div 可接受的区间。两种形式分别为 `q=Div(x*2^k,y)*2^-k` 和 `q=Div(x*2^k,y*2^k)`；前者改变中间商，后者保持商的尺度，必须按具体 FTZ 位置选择。幂二缩放只在不溢出、不发生不允许的舍入/下溢时具有精确性，不能由代数相等推出全 IEEE 等价。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "必须同时约束缩放后的分子、分母、中间商与恢复结果；只证明输入乘法不溢出仍不够",
    "原生乘法对次正规输入的处理也要满足前提，不能假设上移就能恢复已被清零的值",
    "分母为零、exact-zero 谓词、NaN/Inf、符号和最终舍入分别保留",
    "最终结果仍为次正规数时，恢复步骤可能再次 FTZ；只有结果契约或输出容差允许才可进入该路径",
    "舍入倒数乘法是另一项改动，不自动继承本策略的等价性"
  ],
  "schema_version": 2,
  "slug": "bounded-power-two-native-division",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "用受限幂二缩放修复特定 FTZ 敏感区间，从而以原生 Div 替代高代价精确除法。",
  "verification": {
    "correctness": [
      "围绕正规/次正规分界、缩放安全上下界、零分母与舍入分界检查最终输出",
      "确认生成代码减少精确除法辅助工作，并在完整调用中比较性能"
    ],
    "performance": [
      "任何域外输入必须由分派或精确回退覆盖；范围证明失效、特殊值改变或最终误差越界即禁用该路径"
    ],
    "rollback_signals": [
      "输入范围无界、任意次正规数要求全 IEEE 保真、缩放溢出或最终恢复仍违反 FTZ 契约",
      "没有安全 k 时回退精确路径"
    ]
  }
}
-->

# 性能优化策略：有界幂二缩放后使用原生除法

单一优化点：用受限幂二缩放修复特定 FTZ 敏感区间，从而以原生 Div 替代高代价精确除法。

## 1. 原理

当除法的少量合法输入落入 FTZ 敏感段，整条向量链可能被迫采用支持次正规数的昂贵模式。若能证明输入及中间值范围，可选整数 k，把数值迁移到原生 Div 可接受的区间。两种形式分别为 `q=Div(x*2^k,y)*2^-k` 和 `q=Div(x*2^k,y*2^k)`；前者改变中间商，后者保持商的尺度，必须按具体 FTZ 位置选择。幂二缩放只在不溢出、不发生不允许的舍入/下溢时具有精确性，不能由代数相等推出全 IEEE 等价。

## 2. 性能问题模式

热点除法为保留极小输入而使用精确辅助路径，带来较长指令链、寄存器或线程栈开销；实际合法数据域远窄于全浮点域。额外少量缩放乘法可能换掉整套高代价辅助计算。若原生 Div 已足够或整体受带宽限制，则没有对应机会。

## 3. 正确性红线

必须同时约束缩放后的分子、分母、中间商与恢复结果；只证明输入乘法不溢出仍不够。原生乘法对次正规输入的处理也要满足前提，不能假设上移就能恢复已被清零的值。分母为零、exact-zero 谓词、NaN/Inf、符号和最终舍入分别保留。最终结果仍为次正规数时，恢复步骤可能再次 FTZ；只有结果契约或输出容差允许才可进入该路径。舍入倒数乘法是另一项改动，不自动继承本策略的等价性。

## 4. 泛化条件

适用：存在可证明的分子分母范围、安全整数缩放指数 k，以及允许原生除法误差的最终输出契约；精确除法是计算热点。

不适用：输入范围无界、任意次正规数要求全 IEEE 保真、缩放溢出或最终恢复仍违反 FTZ 契约。没有安全 k 时回退精确路径。

## 5. 实施步骤

1. 标出 FTZ 发生在输入、除法中间量还是结果，写出全部上下界。
2. 推导安全 k 的交集，选择分子上移后恢复或分子分母同移，不把固定 k 当通用常量。
3. 保留零值及特殊值分支，在满足范围条件的路径启用 native Div。
4. 独立检查缩放、Div、恢复和最终转换的误差传播，并核对生成的辅助调用与栈变化。

## 6. LLM 前置问题

- 范围来自输入合同与算术上界，还是仅来自观察到的数据？
- 每一步的 FTZ、溢出和舍入边界能否给出明确结论？
- 新增乘法是否比被替代的精确路径便宜，编译器是否保留预期形式？

## 7. 验收标准

围绕正规/次正规分界、缩放安全上下界、零分母与舍入分界检查最终输出。确认生成代码减少精确除法辅助工作，并在完整调用中比较性能。任何域外输入必须由分派或精确回退覆盖；范围证明失效、特殊值改变或最终误差越界即禁用该路径。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：以安全幂二缩放迁移FTZ敏感中间值，使用native Div替代昂贵精确除法。
适用：已知分子分母与中间商范围；存在安全整数指数k；最终契约允许原生除法误差。
限制：同时约束乘法、商与恢复结果；保留零及特殊值；任意次正规数全IEEE保真不可套用；无安全k则回退。
范围：有界数值链的FTZ敏感除法。
检索词：FTZ、native Div、power-of-two scaling、range proof、subnormal
机会：少量极小输入迫使整条热点除法采用昂贵辅助链，增加寄存器或线程栈。
代价：增加缩放乘法与范围条件；恢复步骤仍可能FTZ，需计入最终误差。
