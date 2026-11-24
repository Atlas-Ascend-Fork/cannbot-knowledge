---
type: Optimization
title: 直接以窄浮点原始编码归约绝对值最大值
description: 把逐元素提升再求最大值改为原始 uint16 编码归约，仅转换最终幅值。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/raw-narrow-code-maxabs-reduction.md
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
      "需要在归约前执行浮点算术",
      "编码顺序未证明"
    ],
    "required_conditions": [
      "FP16/BF16非NaN正幅值编码与数值单调一致",
      "目标支持uint16归约",
      "特殊值语义有显式处理"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "per-element-widening",
      "wide-reduction-lanes"
    ],
    "pattern": "raw-code-maxabs",
    "structure": [
      "FP16-BF16",
      "uint16",
      "reduce-before-convert"
    ]
  },
  "generality": "pattern",
  "id": "RAW-NARROW-CODE-MAXABS-REDUCTION",
  "implementation_steps": [
    "以位重解释读取 uint16，清符号位；另行形成有效 lane 与 NaN 谓词。",
    "选择窄 lane 归约布局，依据目标向量宽度计算 pitch，核对 UB 与尾部空间。",
    "归约幅值编码和必要特殊值状态，再按输入 dtype 重解释最终编码。",
    "只提升每行最终幅值；连接原有后续统计、缩放或归一化消费链。"
  ],
  "intent": "输入本为 16 位，统计链却先整行 Cast 到 FP32，再 Abs、ReduceMax，扩大 UB 中间量与归约指令重复数。",
  "mechanism": "清除窄浮点编码符号位，以无符号整数完成最大归约，只转换最终标量。",
  "name": "直接以窄浮点原始编码归约绝对值最大值",
  "operator_scope": "FP16/BF16 绝对值最大归约，目标支持 uint16 比较归约，数据能合法组成向量且特殊值处理可配套。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "FP16/BF16 的非 NaN 正数编码按 uint16 比较时与数值大小单调一致。按位清除符号位得到绝对值编码后，最大编码就是绝对值最大值的编码。整行归约可在窄整数域完成，最后才按原始浮点类型重解释并提升到 FP32。这里不执行低精度浮点算术，也不将 BF16 位型当作 FP16 数值；减少的是逐元素转换和宽 lane 归约成本。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "NaN 编码大于 Inf，直接整数最大值会把 NaN 当作幅值；必须按既定传播或忽略契约显式处理，不能以整数归约自然结果代替语义",
    "无效 lane 清为最大归约的单位元零，并屏蔽其 NaN 标志",
    "保留 Inf、全零行及最小非正规数语义；不得经浮点绝对值操作触发意外 FTZ",
    "最终转换只处理胜出编码，后续缩放、舍入和饱和规则继续保持原契约"
  ],
  "schema_version": 2,
  "slug": "raw-narrow-code-maxabs-reduction",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "把逐元素提升再求最大值改为原始 uint16 编码归约，仅转换最终幅值。",
  "verification": {
    "correctness": [
      "检查全部窄编码的非 NaN 幅值排序，覆盖非正规数、±0、Inf、NaN 与不同尾长",
      "确认中间缓冲和 Cast 工作量实际减少"
    ],
    "performance": [
      "将 pitch 改动与窄编码改动分开比较，并按完整消费链计时；因 padding、特殊值扫描或布局组装回退时收紧路径条件"
    ],
    "rollback_signals": [
      "最大值之前必须执行真实浮点算术，输入编码不是对应浮点格式，或任意跨步布局的组装成本超过节省",
      "跨步路径应保留独立回退"
    ]
  }
}
-->

# 性能优化策略：直接以窄浮点原始编码归约绝对值最大值

单一优化点：把逐元素提升再求最大值改为原始 uint16 编码归约，仅转换最终幅值。

## 1. 原理

FP16/BF16 的非 NaN 正数编码按 uint16 比较时与数值大小单调一致。按位清除符号位得到绝对值编码后，最大编码就是绝对值最大值的编码。整行归约可在窄整数域完成，最后才按原始浮点类型重解释并提升到 FP32。这里不执行低精度浮点算术，也不将 BF16 位型当作 FP16 数值；减少的是逐元素转换和宽 lane 归约成本。

## 2. 性能问题模式

输入本为 16 位，统计链却先整行 Cast 到 FP32，再 Abs、ReduceMax，扩大 UB 中间量与归约指令重复数。若后续仅使用每行一个最大幅值，逐元素提升没有消费价值。窄归约可能提高每次处理的有效元素数，但行 pitch 和尾部对齐也会改变资源占用，需分别评估。

## 3. 正确性红线

NaN 编码大于 Inf，直接整数最大值会把 NaN 当作幅值；必须按既定传播或忽略契约显式处理，不能以整数归约自然结果代替语义。无效 lane 清为最大归约的单位元零，并屏蔽其 NaN 标志。保留 Inf、全零行及最小非正规数语义；不得经浮点绝对值操作触发意外 FTZ。最终转换只处理胜出编码，后续缩放、舍入和饱和规则继续保持原契约。

## 4. 泛化条件

适用：FP16/BF16 绝对值最大归约，目标支持 uint16 比较归约，数据能合法组成向量且特殊值处理可配套。

不适用：最大值之前必须执行真实浮点算术，输入编码不是对应浮点格式，或任意跨步布局的组装成本超过节省。跨步路径应保留独立回退。

## 5. 实施步骤

1. 以位重解释读取 uint16，清符号位；另行形成有效 lane 与 NaN 谓词。
2. 选择窄 lane 归约布局，依据目标向量宽度计算 pitch，核对 UB 与尾部空间。
3. 归约幅值编码和必要特殊值状态，再按输入 dtype 重解释最终编码。
4. 只提升每行最终幅值；连接原有后续统计、缩放或归一化消费链。

## 6. LLM 前置问题

- 逐元素提升后的值是否还有其他消费者？
- 目标整数归约的 lane 宽度、掩码粒度与浮点路径是否一致？
- 增大 pitch 是否使行批量或双缓冲容量下降？

## 7. 验收标准

检查全部窄编码的非 NaN 幅值排序，覆盖非正规数、±0、Inf、NaN 与不同尾长。确认中间缓冲和 Cast 工作量实际减少。将 pitch 改动与窄编码改动分开比较，并按完整消费链计时；因 padding、特殊值扫描或布局组装回退时收紧路径条件。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：清除窄浮点原始编码符号位，以uint16归约最大幅值，仅将最终编码提升FP32。
适用：FP16/BF16绝对值最大归约；目标支持uint16归约；特殊值处理可配套。
限制：NaN按原传播或忽略契约显式处理；尾lane为零；保留非正规数位型；不得混解释BF16与FP16。
范围：窄浮点统计链的绝对值最大归约。
检索词：uint16、FP16、BF16、ReduceMax、raw bits、FTZ
机会：逐元素Cast到FP32后Abs和ReduceMax，扩大中间量与宽lane归约成本。
代价：窄lane布局与pitch可能增加padding和UB占用；特殊值扫描也有成本。
