---
type: Optimization
title: 按访存角色选择随机目标覆盖写策略
description: 只把 SIMT 随机目标的普通覆盖写改为 asc_stcg，独立评估其存储策略。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.implementation.atomic
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/simt-random-target-store-policy.md
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
      "用普通写代替原子或归约",
      "将缓存提示当作同步或顺序保证"
    ],
    "required_conditions": [
      "目标平台支持对应类型GM指针的asc_stcg",
      "目标操作是语义已成立的随机覆盖写"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "random-target-store",
      "store-policy-mismatch"
    ],
    "pattern": "simt-random-target-store-policy",
    "structure": [
      "SIMT",
      "overwrite",
      "role-specific-cache-hint"
    ]
  },
  "generality": "pattern",
  "id": "SIMT-RANDOM-TARGET-STORE-POLICY",
  "implementation_steps": [
    "分开识别连续复制、随机覆盖、原子更新及结果读取的角色。",
    "仅替换随机覆盖路径的目标 store，保持地址、载荷与同步逻辑。",
    "检查生成指令和各数据类型支持情况，对不支持的路径保留普通写。",
    "按目标域大小、重复度和复用强弱比较完整调用，并检查其它阶段的间接影响。"
  ],
  "intent": "源数据顺序读取，目标地址由运行时索引产生，写请求分散且行复用弱；同一实现却对复制、覆盖写及归约使用统一访存策略。",
  "mechanism": "只对SIMT随机目标覆盖写选择专用存储策略，按拷贝、覆盖写和原子归约区分访存角色。",
  "name": "按访存角色选择随机目标覆盖写策略",
  "operator_scope": "目标平台与编译器支持对应类型的 GM 指针和 asc_stcg，随机目标覆盖写可单独定位，数据类型的存储语义保持一致。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "连续复制、随机覆盖和原子读改写具有不同的访问局部性。随机目标行在短期内缺少复用时，默认写策略未必合适；使用 asc_stcg 可改变目标存储请求的缓存策略，而不改变目标地址和值。该动作不减少逻辑写入字节，收益取决于实际访问分布和硬件实现，不能仅从指令名称断定某一级缓存的具体根因。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "只修改已经合法的覆盖写，不改变索引解码、步长、数据宽度、存储位型及重复目标的允许结果",
    "asc_stcg 不提供原子性、跨线程同步或额外顺序保证；存在写竞争时，必须由原有语义和并行组织证明合法",
    "不能据此替换原子更新或非原子读改写中的必要同步"
  ],
  "schema_version": 2,
  "slug": "simt-random-target-store-policy",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "只把 SIMT 随机目标的普通覆盖写改为 asc_stcg，独立评估其存储策略。",
  "verification": {
    "correctness": [
      "覆盖数据位型、重复索引、非连续步长与地址边界，确认输出语义一致",
      "生成代码使用预期指令且仅作用于选定路径，完整调用耗时有稳定改善；高复用路径退化时缩小分派范围"
    ],
    "performance": [
      "缓存计数器不足时，仅陈述存储策略与耗时变化，不归因到特定缓存行为"
    ],
    "rollback_signals": [
      "将原子归约路径视为同等受益，或把 MTE 的 GlobalTensor 提示直接等同于 SIMT store",
      "小目标域和高复用访问可能因失去有用缓存或写合并而变慢，提示需按访存角色分派"
    ]
  }
}
-->

# 性能优化策略：按访存角色选择随机目标覆盖写策略

单一优化点：只把 SIMT 随机目标的普通覆盖写改为 asc_stcg，独立评估其存储策略。

## 1. 原理

连续复制、随机覆盖和原子读改写具有不同的访问局部性。随机目标行在短期内缺少复用时，默认写策略未必合适；使用 asc_stcg 可改变目标存储请求的缓存策略，而不改变目标地址和值。该动作不减少逻辑写入字节，收益取决于实际访问分布和硬件实现，不能仅从指令名称断定某一级缓存的具体根因。

## 2. 性能问题模式

源数据顺序读取，目标地址由运行时索引产生，写请求分散且行复用弱；同一实现却对复制、覆盖写及归约使用统一访存策略。随机写阶段占用明显时间，修改普通目标 store 的成本小，适合独立比较默认写与专用提示。

## 3. 正确性红线

只修改已经合法的覆盖写，不改变索引解码、步长、数据宽度、存储位型及重复目标的允许结果。asc_stcg 不提供原子性、跨线程同步或额外顺序保证；存在写竞争时，必须由原有语义和并行组织证明合法。不能据此替换原子更新或非原子读改写中的必要同步。

## 4. 泛化条件

适用：目标平台与编译器支持对应类型的 GM 指针和 asc_stcg，随机目标覆盖写可单独定位，数据类型的存储语义保持一致。

不适用：将原子归约路径视为同等受益，或把 MTE 的 GlobalTensor 提示直接等同于 SIMT store。小目标域和高复用访问可能因失去有用缓存或写合并而变慢，提示需按访存角色分派。

## 5. 实施步骤

1. 分开识别连续复制、随机覆盖、原子更新及结果读取的角色。
2. 仅替换随机覆盖路径的目标 store，保持地址、载荷与同步逻辑。
3. 检查生成指令和各数据类型支持情况，对不支持的路径保留普通写。
4. 按目标域大小、重复度和复用强弱比较完整调用，并检查其它阶段的间接影响。

## 6. LLM 前置问题

- 目标是纯覆盖写，还是必须保留每次贡献的读改写？
- 重复索引的写竞争是否合法，是否另需原子或顺序控制？
- 写行是否很快再次读取，目标域是否具有强局部性？

## 7. 验收标准

覆盖数据位型、重复索引、非连续步长与地址边界，确认输出语义一致。生成代码使用预期指令且仅作用于选定路径，完整调用耗时有稳定改善；高复用路径退化时缩小分派范围。缓存计数器不足时，仅陈述存储策略与耗时变化，不归因到特定缓存行为。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：仅将SIMT随机目标的普通覆盖写改为asc_stcg，按访存角色选择存储策略。
适用：目标平台与编译器支持对应类型GM指针的asc_stcg，随机覆盖写语义已成立。
限制：保留地址、位型和重复目标语义；提示不提供同步、顺序或原子性；不得替换原子归约。
范围：SIMT随机目标覆盖写路径。
检索词：asc_stcg、SIMT、GM指针、随机覆盖写、存储策略、访存角色
机会：源顺序读取而目标分散、写行复用弱，复制与随机更新却使用统一访存策略。
代价：小目标域或高复用访问可能失去有用缓存和写合并，不减少逻辑写字节。
