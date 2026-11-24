---
type: Optimization
title: 重复状态变换的精确末状态摘要
description: 证明重复变换的末状态、步数及附加量可精确摘要后，以摘要替代逐步推进。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/exact-repeated-state-transition-collapse.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "exact-repeated-state-transition-collapse",
  "slug": "exact-repeated-state-transition-collapse",
  "name": "重复状态变换的精确末状态摘要",
  "classification": "validated_strategy",
  "generality": "pattern",
  "phase": [
    "design",
    "tuning"
  ],
  "revision": "2026-11-09-blind-feedback-v2",
  "evidence_policy": "具名来源与测量由独立证据台账保存，修订指导本身不宣称新增性能验证。"
}
-->

# 重复状态变换的精确末状态摘要

## 原理与适用条件

若下游仅使用重复变换的末状态和必要的附加量，可以用一次精确摘要代替逐步推进。先写出单步变换、终止谓词和附加状态更新，再证明摘要给出的步数是原过程首次满足停止条件的步数，结果等于按这个步数组合原变换。

有限位归一化可以作为候选：当每步只移除一个可约位因子，且中间状态不可观察时，可考虑一次求得可移除数量和归一化后的状态。是否适用由原变换、实际类型与目标原语共同决定；如果只能计算主值，不能恢复计数、标志或后续需要的状态，摘要还不完整。

## 正确性红线

- 保持首次终止、零步分支、异常、符号、类型提升、溢出及后续消费结果。中间存储、同步、随机状态、舍入或异常顺序若可观察，必须证明跳过后仍满足原契约。
- 区分无需推进、零编码、原语在零上未定义，以及移位量达到类型宽度。先判合法域，再调用摘要原语；域外保留原精确路径。宽类型的扫描和移位须在实际类型中证明，不能由窄原语的结果反推。
- 对浮点等带逐步舍入的状态变换，数学式等价不足以证明执行结果等价。摘要不得通过改变检查规则或把未定义域当成常规值来通过验收。

## 实施与代价

先写一个独立状态模型，比较逐步推进与摘要的末状态、步数和所有附加量。随后在原先的初始化或每轮归一化位置引入摘要和精确回退。覆盖零步、最短和长推进、宽度及符号边界、回退与后续消费；检查实际输入是否进入摘要路径。

计入摘要原语、合法域检查、分派和活跃状态成本。原循环多数只推进少量步骤时，直接执行可能更省；确认生成代码是否发生隐式宽化或软件展开，再用完整调用测量判断。与直接终止、窄域计算组合时分别保留等价证明，未消融的收益按整体归档。

## 检索卡（短卡）

动作：证明重复变换的末状态、步数及附加量可精确摘要后，以摘要替代逐步推进。
适用：中间状态不可观察且完整状态组合可证明等价。
限制：区分零步、零输入及非法扫描或移位；宽类型独立证明。
范围：有限位状态归一化与重复变换。
检索词：末状态摘要、附加计数、位扫描、零步、组合等价
机会：可与直接终止和窄域计算组合，收益按整体记录。
代价：摘要、门检查及资源成本可能超过少量原推进。
