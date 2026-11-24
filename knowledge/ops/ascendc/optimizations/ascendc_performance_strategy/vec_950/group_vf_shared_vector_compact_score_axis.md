---
type: Optimization
title: 组级VF共享扫描与紧凑结果轴向量化
description: 将逐行VF扫描合入组级VF，以小行块共享只读向量，并将标量结果紧凑排列到连续lane供下游并行处理。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/group-vf-shared-vector-compact-score-axis.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "group-vf-shared-vector-compact-score-axis",
  "slug": "group-vf-shared-vector-compact-score-axis",
  "name": "组级VF共享扫描与紧凑结果轴向量化",
  "classification": "validated_strategy",
  "generality": "dataflow_pattern",
  "validation_scope": "组合机制已有验证；迁移须核对目标架构、工具链、数值契约和资源预算并重新配对测量",
  "feature_signature": {
    "pattern": "group-vf-shared-vector-compact-score-axis",
    "structure": [
      "group-vf-batching",
      "shared-vector-microtile",
      "compact-result-axis"
    ]
  },
  "verification": {
    "status": "validated_as_combination",
    "attribution": "组合内子动作未逐项独立消融，不承诺单项或跨场景收益",
    "migration_required": true
  }
}
-->

# 性能优化策略：组级VF共享扫描与紧凑结果轴向量化

> 组合优化点：把逐行发起的独立扫描合入组级VF，在小行块中共享只读向量，并把独立标量结果紧凑排列到连续lane，使下游沿结果轴并行处理。

## 1. 原理

相邻行沿相同列方向扫描，并读取相同的只读向量。以小行块为单位把列块循环放到外层，每个列块只加载一次共享向量，同时推进多行独立累加器；行内的元素覆盖与累加次序保持不变。行循环与不足一块的尾行处理放在同一次VF中，摊薄逐行调度。

每行归约产生的标量紧凑写入连续lane，下游可按结果轴执行max、exp、sum等同构运算，而不是每个标量占一整向量槽后逐个广播。组级调用次数由实际驻留窗口和消费者决定；不能仅凭分组就假设整段只有一次VF调用。

共享扫描、调用粒度与结果布局共同构成该策略。若只采用其中一项，应单独检验其资源、精度和性能。

## 2. 性能问题模式

- 每行独立，却重复VF发起、mask构建和循环准备。
- 相邻行重复加载同一UB向量，已有局部驻留未转化为寄存器复用。
- 独立标量结果稀疏存储，下游多数lane处理相同广播值。

## 3. 正确性红线

- 保持每行归约的元素覆盖、数据类型和原累加次序；共享值在整个小行块内必须不变。
- 结果生产者与全部消费者一起迁移布局；核对Reduce输出布局、lane广播、标量存储和尾mask语义。
- 完整向量加载必须有真实可访问的guard；不能用结果mask替代越界访问保护。
- 生产者落盘、跨VF消费和scratch复用的RAW/WAR需明确；不得假定不同VF天然顺序可见。
- 保留奇数尾行和不足一块路径；结果数超出单向量容量时分块或回退，禁止截断。

## 4. 泛化条件

适用：相邻独立行共享只读向量；每行产生少量标量结果且下游同构；寄存器和scratch预算允许批处理。

不适用或需回退：存在行间依赖、共享值随行变化、工作不足以摊薄调度，或布局容量与可见性没有合法实现。小行块大小由目标编译器、寄存器压力、驻留窗口和尾部开销共同确定。

## 5. 实施步骤

1. 冻结原实现，定位逐行VF、重复加载和结果消费者，确认哪些行真正独立。
2. 按资源预算选择小行块，用组级VF包住主循环与尾行处理，按列块共享只读向量。
3. 统一迁移结果存储、下游结果轴计算及全部消费者，补齐guard、mask与可见性。
4. 比较VF调用、共享向量加载、寄存器及UB占用，覆盖结果容量边界和尾部。
5. 精度通过后同设备同输入交替配对测量，按数据域保留或回退。

## 6. LLM 前置问题

- 共享值在哪个循环层级不变，行内与行间依赖分别是什么？
- 当前调度与重复加载是否位于热点，编译器是否已经消除它们？
- 结果轴是否能合法装入目标向量，超容量与尾行路径如何覆盖？
- 所有布局消费者和跨VF可见性是否同步更新？

## 7. 验收标准

正确性：保持接口语义与原精度阈值，覆盖尾部、容量边界、空域及策略涉及的状态和数值边界。使用正确性对照验证所有受影响路径，不仅验证主路径。

性能：冻结前后源码与二进制，在同设备、同输入、同构建配置下按配对测量协议比较设备Task Duration；先对相同输入域内的多次结果取均值，再按约定跨域聚合，并检查域内回归。

决策：精度、越界、资源或同步检查失败时先修复或回退；没有可信性能收益时保留原路径。组合已有验证不等于其中任一子动作独立有效，单独迁移子动作需要独立验证。

## 检索卡（短卡）

动作：将逐行VF扫描合入组级VF，以小行块共享只读向量，并将标量结果紧凑排列到连续lane供下游并行处理。
适用：相邻行独立且共享只读向量，每行产生少量标量结果，下游同构，寄存器与scratch预算充足。
限制：保持行内累加次序；迁移全部布局消费者；核对Reduce输出、guard和跨VF可见性；尾行与超容量必须覆盖。
范围：逐行扫描、分组归约、标量结果的同构后处理。
检索词：组级VF、共享向量、寄存器复用、紧凑结果轴、Reduce、lane、尾mask。
机会：逐行VF重复调度和加载共享向量，稀疏标量结果使下游lane重复处理广播值。
代价：寄存器生命周期和布局迁移复杂度增加；小任务可能无法摊薄固定开销。
