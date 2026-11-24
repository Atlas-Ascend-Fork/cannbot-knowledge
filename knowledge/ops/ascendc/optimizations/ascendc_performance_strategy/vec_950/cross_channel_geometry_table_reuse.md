---
type: Optimization
title: 跨通道几何元数据物化复用
description: 把每个通道重复的几何解码提到独立生产阶段，物化为跨通道复用的 GM 表。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/cross-channel-geometry-table-reuse.md
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
      "坐标或边界语义随通道变化",
      "新增表流量超过省下的重复计算"
    ],
    "required_conditions": [
      "几何元数据与通道无关且跨通道重复使用",
      "额外表空间及完整调用成本可接受"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "repeated-coordinate-decode",
      "repeated-weight-generation"
    ],
    "pattern": "cross-channel-geometry-table-reuse"
  },
  "generality": "pattern",
  "id": "cross-channel-geometry-table-reuse",
  "implementation_steps": [
    "分离几何与数据通道计算，逐字段证明其与通道无关。",
    "确定有效邻域数、偏移宽度、权重类型及 SoA 索引，推导总空间。",
    "生产完整表，消费者叠加通道基址并维持原读取及累加顺序。",
    "比较完整调用后设置由规模、模式和容量决定的门控，保留融合回退。"
  ],
  "intent": "各通道重复执行坐标解码、整浮点转换、取整及边界分支，计算链长而相同输入被反复解释。",
  "mechanism": "将与通道无关的坐标、偏移和权重预计算成GM表，再供所有通道消费。",
  "name": "跨通道几何元数据物化复用",
  "operator_scope": "C 个通道共享几何，且省下的 (C-1)*P 次解码成本，大于额外启动、P 项表写入和 C*P 项表读取成本；表总字节数及偏移乘积均在容量和整数范围内。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "多通道读取同一空间位置时，坐标变换、边界处理、邻域偏移和插值权重往往与通道无关。先对 P 个空间点各计算一次，将邻域偏移和权重写成 SoA 表，再由通道消费者加载表并访问输入。省掉的是 C 个通道之间的几何重算，代价是一次生产启动、表写入和消费者表读取。该机制使用跨阶段 GM 物化，不等同于单核内寄存器或 UB 驻留。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "表只保存通道无关的相对空间偏移，消费者另加批次及通道基址；合法跨步按实际物理布局计算，地址宽度须覆盖最大偏移",
    "边界标记不可与合法地址混淆",
    "坐标运算顺序、取整方式、权重精度及邻域累加顺序须符合原契约",
    "workspace 每次调用独占，生产完成后才消费，异步调用不能复用尚在使用的表"
  ],
  "schema_version": 2,
  "slug": "cross-channel-geometry-table-reuse",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "把每个通道重复的几何解码提到独立生产阶段，物化为跨通道复用的 GM 表。",
  "verification": {
    "correctness": [
      "覆盖各边界模式、取整临界点、退化空间维、合法跨步和并发调用"
    ],
    "performance": [
      "分别检查生产及消费，再比较含表分配与全部启动的完整路径；拒绝只有消费阶段变快的方案"
    ],
    "rollback_signals": [
      "少通道、小工作量、通道依赖几何、表无法容纳，或表流量主导",
      "不同邻域模式的有效字段数不同，应按字段数重新预算，不能套固定通道阈值"
    ]
  }
}
-->

# 性能优化策略：跨通道几何元数据物化复用

单一优化点：把每个通道重复的几何解码提到独立生产阶段，物化为跨通道复用的 GM 表。

## 1. 原理

多通道读取同一空间位置时，坐标变换、边界处理、邻域偏移和插值权重往往与通道无关。先对 P 个空间点各计算一次，将邻域偏移和权重写成 SoA 表，再由通道消费者加载表并访问输入。省掉的是 C 个通道之间的几何重算，代价是一次生产启动、表写入和消费者表读取。该机制使用跨阶段 GM 物化，不等同于单核内寄存器或 UB 驻留。

## 2. 性能问题模式

各通道重复执行坐标解码、整浮点转换、取整及边界分支，计算链长而相同输入被反复解释。通道数增加时重复工作放大；几何简单或数据访问已饱和时，新增表流量可能更慢。SoA 可让相邻点按同一邻域项合并访问，但布局仍需匹配消费者调度。

## 3. 正确性红线

表只保存通道无关的相对空间偏移，消费者另加批次及通道基址；合法跨步按实际物理布局计算，地址宽度须覆盖最大偏移。边界标记不可与合法地址混淆。坐标运算顺序、取整方式、权重精度及邻域累加顺序须符合原契约。workspace 每次调用独占，生产完成后才消费，异步调用不能复用尚在使用的表。

## 4. 泛化条件

适用：C 个通道共享几何，且省下的 (C-1)*P 次解码成本，大于额外启动、P 项表写入和 C*P 项表读取成本；表总字节数及偏移乘积均在容量和整数范围内。

不适用或需退回：少通道、小工作量、通道依赖几何、表无法容纳，或表流量主导。不同邻域模式的有效字段数不同，应按字段数重新预算，不能套固定通道阈值。

## 5. 实施步骤

1. 分离几何与数据通道计算，逐字段证明其与通道无关。
2. 确定有效邻域数、偏移宽度、权重类型及 SoA 索引，推导总空间。
3. 生产完整表，消费者叠加通道基址并维持原读取及累加顺序。
4. 比较完整调用后设置由规模、模式和容量决定的门控，保留融合回退。

## 6. LLM 前置问题

哪些字段真正可共享？表会读写多少字节？通道数足以摊薄启动吗？地址和哨兵是否安全？融合基线是否已受带宽限制？

## 7. 验收标准

覆盖各边界模式、取整临界点、退化空间维、合法跨步和并发调用。分别检查生产及消费，再比较含表分配与全部启动的完整路径；拒绝只有消费阶段变快的方案。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：独立生成通道无关的坐标、偏移和权重SoA表，再由各通道读取复用。
适用：几何跨通道相同；省下重复解码超过启动与表流量；表容量和整数范围合法。
限制：偏移须加实际批次及通道基址；保持取整、边界和累加顺序；每调用独占表且生产后消费。
范围：多通道空间访问的坐标及权重生成环节。
检索词：SoA、GM表、cross-channel、geometry、offset、weight
机会：各通道重复坐标变换、取整及边界分支，计算链长。
代价：额外生产启动、表分配及写读流量；几何简单时可能回退。
