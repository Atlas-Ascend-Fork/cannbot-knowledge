---
type: Optimization
title: 派发斜坡与离散工作组联合选核模型
description: 联合派发曲线与每核离散组数建立成本模型，枚举合法启核数并保留饱和域并行度。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/dispatch-workload-core-count-model.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "dispatch-workload-core-count-model",
  "name": "派发斜坡与离散工作组联合选核模型",
  "classification": "conditional_strategy",
  "slug": "dispatch-workload-core-count-model",
  "generality": "dataflow_pattern",
  "feature_signature": {
    "pattern": "dispatch-workload-core-count-model"
  },
  "verification": {
    "status": "no_independent_dispatch_change",
    "attribution": "方法已做调度对照，但未建立独立新增收益；仅在实际启核变化且配对收益成立时采用。",
    "migration_required": true
  }
}
-->

# 性能优化策略：派发斜坡与离散工作组联合选核模型

> 单一优化点：同时估计派发开销和每核离散工作组数量，枚举合法启核数选择较低总成本，而非只按硬件最大核数发射。

## 1. 原理

对于可独立切分为G个工作组的数据流，启核数n既影响派发成本，也影响每核承担的ceil(G/n)组工作。以目标环境测量拟合D(n)和单组工作量C，比较T(n)=D(n)+ceil(G/n)*C；D(n)可从截距与斜坡起步，但必须允许目标环境不满足线性假设。

在合法核数候选中选择模型较优项，并通过完整设备耗时验证。候选至少覆盖有效上限；模型未改变实际调度时不能把测量抖动算成独立收益。参数来自目标资源与工作量，不跨环境复用固定斜率或阈值。

## 2. 性能问题模式

- 小任务启用大量核，每核准备和派发占主要耗时。
- 仅按字节数缩核，忽略重复计算和离散组数导致的阶梯变化。
- 模型看似不同，但最终Block Num与原路径一致。

## 3. 正确性红线

- 先证明工作组独立，核数变化不会破坏所有权、跨核同步、覆盖和输出顺序。
- 总组数和每核组数均向上取整；空域短路、空核安全退出，尾组恰好覆盖一次。
- 索引乘加用足够宽的整数；核数满足硬件上限和有效组数上限。
- 派发曲线与组成本需要同设备测量，工作组尺寸、dtype或状态容量改变后重新校准。
- 保留饱和工作域的有效并行度；实际核数不变时不计新增收益，不额外引入未验证分派。

## 4. 泛化条件

适用：任务能按独立工作组切分，派发成本可测，存在多个合法启核数且单组工作量可估计。

不适用或需回退：跨核耦合、动态队列已经解决调度、映射不能随核数改变、模型失准，或实际调度未变化。

## 5. 实施步骤

1. 固定计算路径、组大小和工具链，测量启核数与设备耗时关系。
2. 建立派发曲线和单组成本，枚举合法候选并保留有效上限。
3. 以向上取整构造每核区间，验证覆盖、不重叠和尾组。
4. 从profiling读取实际Block Num，对照模型是否真正改变分派。
5. 分别检验固定开销域和饱和域，收益不可信或域内回退时恢复原策略。

## 6. LLM 前置问题

- 被改变的是实际Block Num还是仅主机端公式？
- ceil带来的组数阶梯与尾组如何影响单核工作量？
- 派发模型在拟合范围外是否仍成立？
- 缩核后是否降低带宽或计算饱和度？

## 7. 验收标准

正确性：保持原接口、精度阈值和输出布局，覆盖空域、尾部、容量边界、重复值和所有受影响分支。先验证语义与合法访问，再判断收益；不放宽阈值以迁就新路径。

性能：冻结前后源码和二进制，同设备、同输入、同工具链，依照配对测量协议比较设备Task Duration；每个输入域先取均值，再按约定跨域聚合，保留域内回归和剔除补测记录。迁移到新的资源、布局或数值域必须重新验证。

决策：资源、越界、同步或精度检查失败时修复或回退；没有可信收益时保留原路径。组合验证不能推出任何子动作独立有效。

## 8. 与相邻策略的边界

与[launch-core-count-convergence](launch_core_count_convergence.md)按每核预算收敛的方向相关，本策略显式加入离散组数的ceil阶梯与派发曲线联合枚举，要求核对实际调度变化；不复用已有文档的固定每核预算。

## 检索卡（短卡）

动作：联合派发曲线与每核离散组数建立成本模型，枚举合法启核数并保留饱和域并行度。
适用：工作组独立，派发可测且存在多个合法核数，组成本可估计。
限制：分组均用ceil且覆盖不重叠；模型本机校准；实际核数未变不计新增收益。
范围：独立行组或工作块的多核调度。
检索词：Block Num、ceil、dispatch、成本模型、工作组
机会：固定派发成本主导，或仅按字节预算选核忽略离散工作量。
代价：模型与校准有成本；缩核可能降低饱和度，仅条件采用。
