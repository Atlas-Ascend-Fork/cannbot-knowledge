---
type: Optimization
title: 统一互补尾部有理式以消除双套近似链
description: 扩大一套互补函数有理近似的合法区间，删除另一套近似及其除法、比较和选择。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/uniform-complementary-tail-rational.md
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
      "要求全域逐位数学库一致",
      "扩大域后分母无正下界",
      "只有稳定性改善而无被删除计算"
    ],
    "required_conditions": [
      "可定义有限参数域与输出容差",
      "同一erfc有理式在整个目标域满足误差预算",
      "双套近似链为计算热点"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "duplicated-polynomial-pairs",
      "duplicated-divide",
      "branch-selection"
    ],
    "pattern": "uniform-complementary-rational",
    "structure": [
      "bounded-domain",
      "erfc",
      "direct-tail"
    ]
  },
  "generality": "pattern",
  "id": "UNIFORM-COMPLEMENTARY-TAIL-RATIONAL",
  "implementation_steps": [
    "写出最终输出对互补尾部 r 的依赖，区分直接小尾和互补大分支。",
    "为 `0<=a<=A` 构造统一有理式，分析分母下界与误差传播到最终输出的上界。",
    "以一套 Horner 分子/分母和一次 Div 生成 r，删除另一套近似与路径选择。",
    "保留独立特殊值及域外处理，按原始输入完成最终乘法和转换。"
  ],
  "intent": "向量路径为避免分歧而同时执行大小参数两套近似，最后 Select，导致两套 Horner 链和 Div 均付费。",
  "mechanism": "在有界参数域使用一套互补函数有理近似，直接计算小尾部并删除另一套分子分母和选择。",
  "name": "统一互补尾部有理式以消除双套近似链",
  "operator_scope": "误差函数型复合变换具有互补尾部结构、可定义有限参数域、同一有理式满足整个域的最终输出容差，且双套近似为计算热点。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "当函数可由 erf/erfc 互补关系表达时，小参数路径与尾部路径常分别计算不同的分子、分母再选择结果。若同一 erfc 有理式在完整有界域 `0<=a<=A` 都满足最终输出误差，可统一求 `r=erfc(a)`：小尾部直接消费 r，互补的大分支再由 r 构造。性能收益来自删除一套多项式、除法及选择链，并缩短寄存器活跃区间；直接计算小尾部同时避免 `1-erf(a)` 相消。A 与系数必须由目标误差预算确定，不能把任意尾部近似无条件延伸到零附近。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "扩大近似域后，必须重新约束近零误差、原分界两侧误差和分母最小值；尾部相对误差合格不代表中心区绝对误差合格",
    "最终输出若乘原始输入，保持原始输入和既定舍入顺序，不能用截断参数重建输出",
    "NaN、Inf、±0 及饱和区域单独保持原语义",
    "参数 cap 或尾部置零只能在最终输出误差允许且特殊值处理完整时使用，不能为统一表达任意裁剪"
  ],
  "schema_version": 2,
  "slug": "uniform-complementary-tail-rational",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "扩大一套互补函数有理近似的合法区间，删除另一套近似及其除法、比较和选择。",
  "verification": {
    "correctness": [
      "密集检查近零、原分界、尾部与饱和过渡区，按各 dtype 的最终输出容差验收"
    ],
    "performance": [
      "确认第二套多项式和 Div 已从目标路径消失，核对寄存器占用及完整调用耗时；若统一式增加的阶数或域外分流抵消收益，则保留分段表示"
    ],
    "rollback_signals": [
      "严格全域逐位数学库一致；扩大域造成分母接近零；新近似更高阶以致成本不降；仅改善稳定性而没有减少工作量"
    ]
  }
}
-->

# 性能优化策略：统一互补尾部有理式以消除双套近似链

单一优化点：扩大一套互补函数有理近似的合法区间，删除另一套近似及其除法、比较和选择。

## 1. 原理

当函数可由 erf/erfc 互补关系表达时，小参数路径与尾部路径常分别计算不同的分子、分母再选择结果。若同一 erfc 有理式在完整有界域 `0<=a<=A` 都满足最终输出误差，可统一求 `r=erfc(a)`：小尾部直接消费 r，互补的大分支再由 r 构造。性能收益来自删除一套多项式、除法及选择链，并缩短寄存器活跃区间；直接计算小尾部同时避免 `1-erf(a)` 相消。A 与系数必须由目标误差预算确定，不能把任意尾部近似无条件延伸到零附近。

## 2. 性能问题模式

向量路径为避免分歧而同时执行大小参数两套近似，最后 Select，导致两套 Horner 链和 Div 均付费。即使采用真实分支，混合区间数据仍可能使执行与调度成本偏高。只有统一表达实际删除计算时，才属于本性能策略。

## 3. 正确性红线

扩大近似域后，必须重新约束近零误差、原分界两侧误差和分母最小值；尾部相对误差合格不代表中心区绝对误差合格。最终输出若乘原始输入，保持原始输入和既定舍入顺序，不能用截断参数重建输出。NaN、Inf、±0 及饱和区域单独保持原语义。参数 cap 或尾部置零只能在最终输出误差允许且特殊值处理完整时使用，不能为统一表达任意裁剪。

## 4. 泛化条件

适用：误差函数型复合变换具有互补尾部结构、可定义有限参数域、同一有理式满足整个域的最终输出容差，且双套近似为计算热点。

不适用：严格全域逐位数学库一致；扩大域造成分母接近零；新近似更高阶以致成本不降；仅改善稳定性而没有减少工作量。

## 5. 实施步骤

1. 写出最终输出对互补尾部 r 的依赖，区分直接小尾和互补大分支。
2. 为 `0<=a<=A` 构造统一有理式，分析分母下界与误差传播到最终输出的上界。
3. 以一套 Horner 分子/分母和一次 Div 生成 r，删除另一套近似与路径选择。
4. 保留独立特殊值及域外处理，按原始输入完成最终乘法和转换。

## 6. LLM 前置问题

- 原代码同时计算了几套多项式与除法，统一后实际删除哪些指令？
- 近似区间扩大到零附近后，误差预算由哪个输出区间限制？
- 尾部截断、输入乘法和特殊值处理是否相互独立？

## 7. 验收标准

密集检查近零、原分界、尾部与饱和过渡区，按各 dtype 的最终输出容差验收。确认第二套多项式和 Div 已从目标路径消失，核对寄存器占用及完整调用耗时；若统一式增加的阶数或域外分流抵消收益，则保留分段表示。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：在有界参数域统一使用erfc有理式，直接计算小尾部，删除另一套多项式、Div和选择。
适用：互补尾部结构；0<=a<=A内统一有理式满足最终容差；双套近似为计算热点。
限制：重证近零与分界误差及分母下界；保留原始输入乘法和特殊值；不宣称全域逐位数学库一致。
范围：误差函数型复合变换的分段近似计算。
检索词：erfc、Horner、Div、Select、rational approximation、direct tail
机会：向量路径同时计算大小参数两套分子分母再选择，重复支付多项式和除法。
代价：扩大近似域的误差约束；更高阶或域外分流可能抵消收益。
