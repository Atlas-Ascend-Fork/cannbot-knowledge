---
type: Optimization
title: 低精度原子累加的精度边界
description: 不要把低精度存储类型直接作为多次原子累加的计算精度；优先提升到 FP32 后一次舍回。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.implementation.atomic
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/low-precision-atomic-accumulation-precision-loss.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "替代方案必须计入 FP32 工作区容量、初始化成本、写后可见性和最终转换开销"
    ],
    "excluded_conditions": [
      "已通过最坏输入证明低精度累加满足精度契约，或硬件原子本身采用更高内部精度"
    ],
    "required_conditions": [
      "存在多个值累加到同一低精度目标地址，且算子对误差有明确容限"
    ]
  },
  "applicability_boundary": "",
  "classification": "negative_boundary",
  "created": "2026-08-21",
  "evidence": [],
  "generality": "common",
  "id": "NEG-1",
  "implementation_steps": [
    "构造高冲突、正负抵消和大动态范围输入，量化低精度逐次舍入误差",
    "选择 UB 局部 FP32 累加或 GM FP32 工作区原子累加，保持更新地址映射不变",
    "在所有更新完成并可见后，仅在最终输出阶段转换回低精度 dtype",
    "若资源不允许高精度工作区，保留原正确路径而不是放宽精度阈值"
  ],
  "instance_ids": [],
  "intent": "避免把减少工作区或简化数据流建立在不可接受的累计舍入误差上。",
  "mechanism": "fp16/bf16 直接 SetAtomicAdd（按存储 dtype 逐次舍入）精度不达标，即使每段仅 1-2 次累加；必须 fp32 累加 + 末尾单次舍回。",
  "name": "低精度原子累加的精度边界",
  "op": "seed",
  "operator_class": "",
  "operator_scope": "需要对 fp16、bf16 等低精度目标执行多次并发累加的归约与散射更新",
  "principle": "低精度原子加会在每一次更新后按目标 dtype 舍入，误差随更新次数、数值动态范围和并发归约顺序累积；使用高精度局部或全局工作区，可把多次舍入压缩为最终写回时的一次舍入。",
  "provenance": {
    "skill": "SKILL.md §7 负结果"
  },
  "related_anti_patterns": [],
  "related_seed_ids": [],
  "risks": [
    "高精度工作区增加内存流量与容量压力；浮点归约顺序变化仍需按契约验证"
  ],
  "schema_version": 2,
  "slug": "low-precision-atomic-accumulation-precision-loss",
  "source": "skill",
  "status": "seed",
  "summary": "不要把低精度存储类型直接作为多次原子累加的计算精度；优先提升到 FP32 后一次舍回。",
  "verification": {
    "correctness": [
      "覆盖高重复索引、长归约链、正负抵消、极值和随机输入，并与高精度参考比较"
    ],
    "performance": [
      "把工作区初始化、同步和最终转换计入端到端耗时，不能只测原子更新阶段"
    ],
    "rollback_signals": [
      "精度仍超限、工作区超预算或端到端性能稳定回归时停止采用该替代路径"
    ]
  }
}
-->

# 性能优化策略：低精度原子累加的精度边界

单一优化点：不要把低精度存储类型直接作为多次原子累加的计算精度；优先提升到 FP32 后一次舍回。

## 1. 原理

低精度原子加会在每一次更新后按目标 dtype 舍入，误差随更新次数、数值动态范围和并发归约顺序累积；使用高精度局部或全局工作区，可把多次舍入压缩为最终写回时的一次舍入。

实现机制：fp16/bf16 直接 SetAtomicAdd（按存储 dtype 逐次舍入）精度不达标，即使每段仅 1-2 次累加；必须 fp32 累加 + 末尾单次舍回。

## 2. 性能问题模式

- 优化目标：避免把减少工作区或简化数据流建立在不可接受的累计舍入误差上。
- 适用数据流：需要对 fp16、bf16 等低精度目标执行多次并发累加的归约与散射更新
- Feature signature：`{}`

## 3. 正确性红线

- 高精度工作区增加内存流量与容量压力；浮点归约顺序变化仍需按契约验证

资源与硬件约束：

- 替代方案必须计入 FP32 工作区容量、初始化成本、写后可见性和最终转换开销

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 存在多个值累加到同一低精度目标地址，且算子对误差有明确容限

不适用：

- 已通过最坏输入证明低精度累加满足精度契约，或硬件原子本身采用更高内部精度

## 5. 实施步骤

1. 构造高冲突、正负抵消和大动态范围输入，量化低精度逐次舍入误差
2. 选择 UB 局部 FP32 累加或 GM FP32 工作区原子累加，保持更新地址映射不变
3. 在所有更新完成并可见后，仅在最终输出阶段转换回低精度 dtype
4. 若资源不允许高精度工作区，保留原正确路径而不是放宽精度阈值

## 6. LLM 前置问题

- 目标实现是否满足：存在多个值累加到同一低精度目标地址，且算子对误差有明确容限？
- 是否命中排除条件：已通过最坏输入证明低精度累加满足精度契约，或硬件原子本身采用更高内部精度？

## 7. 验收标准

正确性：

- 覆盖高重复索引、长归约链、正负抵消、极值和随机输入，并与高精度参考比较

性能：

- 把工作区初始化、同步和最终转换计入端到端耗时，不能只测原子更新阶段

回滚信号：

- 精度仍超限、工作区超预算或端到端性能稳定回归时停止采用该替代路径

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`common`
- Related anti-patterns：无

- 尚无归档证据。

## 检索卡（短卡）

动作：将低精度逐次原子累加改为UB局部或GM工作区FP32累加，最终写回时仅舍入一次
适用：同址多次低精度累加且有误差容限；已证明低精度路径满足精度契约时不适用
限制：须计入FP32工作区容量、初始化、写后可见性和最终转换；归约顺序仍须验约
范围：fp16/bf16目标的归约与散射更新
检索词：低精度原子加、目标dtype舍入、UB局部FP32、GM FP32工作区
机会：fp16/bf16目标存在多次并发归约或散射累加
代价：高精度工作区增加内存流量与容量压力
