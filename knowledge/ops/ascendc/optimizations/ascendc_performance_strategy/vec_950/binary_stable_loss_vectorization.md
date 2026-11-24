---
type: Optimization
title: 二类别稳定损失表达与跨样本向量化
description: 将两类别通用指数归约化为稳定差值公式，把并行维度转到样本轴。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/binary-stable-loss-vectorization.md
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
      "soft target",
      "逐样本输出路径直接套用归约布局",
      "未处理额外权重或平滑语义"
    ],
    "required_conditions": [
      "两类别硬标签",
      "类别数据连续且无额外空间归约",
      "输出为sum或mean"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "generic-class-reduction",
      "mixed-control-producer"
    ],
    "pattern": "binary-class-axis-elimination",
    "structure": [
      "two-logits",
      "hard-label",
      "cross-sample-SIMD",
      "sum-count"
    ]
  },
  "generality": "pattern",
  "id": "BINARY-STABLE-LOSS-VECTORIZATION",
  "implementation_steps": [
    "用类别数、布局和归约模式建立专用分派，按样本成批加载两个 logits 与标签。",
    "完整比较忽略标签，建立有效谓词和安全类别选择。",
    "跨样本 SIMD 计算稳定表达；有效 lane 累计 FP32 sum 与足够宽度的 count。",
    "汇总 partial 并执行最终 dtype 转换，保留全忽略与非有限输入的契约分支。"
  ],
  "intent": "类别数已退化到二，仍逐样本运行通用类别归约和混合控制流程，短行向量利用率低；标签判断与计算交错引入额外控制成本。",
  "mechanism": "用两类别差值的稳定标量表达消除类别轴归约，跨样本SIMD并累计局部sum/count。",
  "name": "二类别稳定损失表达与跨样本向量化",
  "operator_scope": "两类别硬标签、类别数据连续且无额外空间归约、输出为 sum 或 mean、局部统计可驻留。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "对于两个 logits x0、x1 与硬标签 t，令 d=x_other-x_target，则损失为 `log1p(exp(-abs(x0-x1)))+max(0,d)`。它消除类别 max、exp 总和与目标值回减的通用链，并避免先形成大值再相减造成近零损失丢失。每个样本成为相同的短算术链，SIMD lane 可直接覆盖多个样本；在生产结果时累计局部 sum/count，最后仅合并每核统计量。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "忽略标签必须先按完整 int64 与 ignore_index 比较，再选择合法类别，不能先截断或索引",
    "soft target、类别权重和平滑项不能假定满足上述表达",
    "有限输入的差值溢出、Inf-Inf 与 NaN 需按原契约分流或显式处理；不能从实数恒等式推断所有浮点特殊值等价",
    "使用 LogOnePlus 或等价保真实现，避免以 `log(1+u)` 丢掉极小损失",
    "mean 按实际有效数量计算，全忽略结果、低精度 sum 溢出与最终舍入保持原语义"
  ],
  "schema_version": 2,
  "slug": "binary-stable-loss-vectorization",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "将两类别通用指数归约化为稳定差值公式，把并行维度转到样本轴。",
  "verification": {
    "correctness": [
      "覆盖大幅值同号/异号、近零损失、完整 int64 忽略值与全忽略输入",
      "编译及执行路径应消除通用类别归约，并能观察跨样本并行"
    ],
    "performance": [
      "计时包含最终合并、标签加载及必要重排；若专用控制或归约开销抵消节省，收紧形状门控"
    ],
    "rollback_signals": [
      "soft target、未推导的权重或平滑语义；逐样本输出不能直接复用归约布局",
      "数据重排代价高时保留通用路径"
    ]
  }
}
-->

# 性能优化策略：二类别稳定损失表达与跨样本向量化

单一优化点：将两类别通用指数归约化为稳定差值公式，把并行维度转到样本轴。

## 1. 原理

对于两个 logits x0、x1 与硬标签 t，令 d=x_other-x_target，则损失为 `log1p(exp(-abs(x0-x1)))+max(0,d)`。它消除类别 max、exp 总和与目标值回减的通用链，并避免先形成大值再相减造成近零损失丢失。每个样本成为相同的短算术链，SIMD lane 可直接覆盖多个样本；在生产结果时累计局部 sum/count，最后仅合并每核统计量。

## 2. 性能问题模式

类别数已退化到二，仍逐样本运行通用类别归约和混合控制流程，短行向量利用率低；标签判断与计算交错引入额外控制成本。若最终只需 sum/mean，逐行损失和有效性数组还会形成多余物化与读回。

## 3. 正确性红线

忽略标签必须先按完整 int64 与 ignore_index 比较，再选择合法类别，不能先截断或索引。soft target、类别权重和平滑项不能假定满足上述表达。有限输入的差值溢出、Inf-Inf 与 NaN 需按原契约分流或显式处理；不能从实数恒等式推断所有浮点特殊值等价。使用 LogOnePlus 或等价保真实现，避免以 `log(1+u)` 丢掉极小损失。mean 按实际有效数量计算，全忽略结果、低精度 sum 溢出与最终舍入保持原语义。

## 4. 泛化条件

适用：两类别硬标签、类别数据连续且无额外空间归约、输出为 sum 或 mean、局部统计可驻留。

不适用：soft target、未推导的权重或平滑语义；逐样本输出不能直接复用归约布局。数据重排代价高时保留通用路径。

## 5. 实施步骤

1. 用类别数、布局和归约模式建立专用分派，按样本成批加载两个 logits 与标签。
2. 完整比较忽略标签，建立有效谓词和安全类别选择。
3. 跨样本 SIMD 计算稳定表达；有效 lane 累计 FP32 sum 与足够宽度的 count。
4. 汇总 partial 并执行最终 dtype 转换，保留全忽略与非有限输入的契约分支。

## 6. LLM 前置问题

- 类别退化条件是否由形状保证，布局是否无需昂贵重排？
- 有效数是否可能超过局部计数类型，跨 tile 如何累加？
- 非有限值与差值溢出如何继续满足原始损失语义？

## 7. 验收标准

覆盖大幅值同号/异号、近零损失、完整 int64 忽略值与全忽略输入。编译及执行路径应消除通用类别归约，并能观察跨样本并行。计时包含最终合并、标签加载及必要重排；若专用控制或归约开销抵消节省，收紧形状门控。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：以稳定二类别差值公式消除类别归约，跨样本SIMD并在生产时累计sum/count。
适用：两类别硬标签、类别数据连续且无额外空间归约、输出为sum或mean；局部统计可驻留。
限制：soft target及未推导权重平滑不可套用；先比较完整int64忽略值；保留全忽略与非有限值语义。
范围：二类别对数损失的生产与最终归约。
检索词：LogOnePlus、SIMD、ignore_index、sum/count、stable loss
机会：两类别仍执行通用max/exp/sum链，短行利用率低且物化逐行中间量。
代价：专用分派、标签加载和最终合并；必要重排可能抵消节省。
