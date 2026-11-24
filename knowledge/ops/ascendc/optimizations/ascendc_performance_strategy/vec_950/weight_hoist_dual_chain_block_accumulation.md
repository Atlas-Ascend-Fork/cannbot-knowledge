---
type: Optimization
title: 权重寄存器提升与分块双链加权累加
description: 把跨列块不变的行权重提前广播到寄存器，以两条独立FMA部分累加链计算并在列块末合并。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/weight-hoist-dual-chain-block-accumulation.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "weight-hoist-dual-chain-block-accumulation",
  "slug": "weight-hoist-dual-chain-block-accumulation",
  "name": "权重寄存器提升与分块双链加权累加",
  "classification": "validated_strategy",
  "generality": "dataflow_pattern",
  "validation_scope": "组合机制已有验证；迁移须核对目标架构、工具链、数值契约和资源预算并重新配对测量",
  "feature_signature": {
    "pattern": "weight-hoist-dual-chain-block-accumulation",
    "structure": [
      "register-weight-hoisting",
      "loop-interchange",
      "dual-fma-dependency-chain"
    ]
  },
  "verification": {
    "status": "validated_as_combination",
    "attribution": "组合内子动作未逐项独立消融，不承诺单项或跨场景收益",
    "migration_required": true
  }
}
-->

# 性能优化策略：权重寄存器提升与分块双链加权累加

> 组合优化点：将每个列块重复广播的行权重提升到有界行块的寄存器中，以两条独立部分累加链计算加权和，再合并结果。

## 1. 原理

原循环按列块遍历行，同一行的权重在不同列块中重复广播，聚合值沿行方向形成一条长FMA依赖链。改为有界行块外层、列块内层：行块权重在进入列块循环前广播到寄存器；偶数、奇数行分别进入独立累加器，在列块末合并。

只有首个行块可以从零开始。后续块将已有聚合值作为一个部分累加器的初值，另一个从零开始，避免丢失之前的贡献。权重无需满足闭式生成条件，但必须在该行块的所有列块间不变。

这种拆分重排了同一归约的加法结合顺序，与仅交错两条原有独立链不同，不能承诺位级不变。

## 2. 性能问题模式

- 权重跨列块不变，却在每个列块重复从UB加载并广播。
- 长FMA依赖链限制指令并发，即使输入已在UB驻留仍存在计算气泡。
- 广播与聚合值往返位于热点，且目标资源允许多个部分累加器。

## 3. 正确性红线

- 接口必须允许浮点重排；要求严格位一致的路径不可直接采用，不能放宽既有精度阈值。
- 验证相消、小值、大值及目标dtype的舍入，不能用数学等价代替数值验证。
- 明确首块清零与后续块续加，保证所有有效行和尾块各贡献一次。
- 权重加载、行指针和mask与有效范围一致；不能依靠输出mask掩盖无效行读取。
- PostUpdate加载与存储聚合值使用独立游标，避免读后存储错位。
- RegTensor数组和#pragma unroll不保证工具链支持；无法可靠展开时使用固定寄存器与编译期条件，并检查spill。

## 4. 泛化条件

适用：行权重跨列块不变；累加链较长且接口允许重排；权重和部分累加器可在寄存器预算内驻留。

不适用或需回退：严格位一致、权重随列块变化、广播已被消除、搬运完全主导，或spill、块调用与末尾合并开销超过节省。行块和部分累加器数量均按目标资源与实测选择，不追求最大块。

## 5. 实施步骤

1. 确认权重的不变层级、精度契约和当前广播/累加链热点。
2. 按寄存器预算选有界行块，将权重广播移到列块循环外。
3. 建立两条独立FMA链，区分首块初始化和后续块续加，在列块末合并。
4. 核对独立load/store游标、奇数尾行和剩余块，检查编译展开与资源报告。
5. 完成精度与数值边界检查后，配对比较全部受影响域，资源或性能恶化时缩块或回退。

## 6. LLM 前置问题

- 权重是否在整个驻留行块的列块遍历期间保持不变？
- 接口允许哪种重排，哪些数值域最容易暴露相消误差？
- 首块与后续块怎样保留已有聚合值，游标是否独立？
- 块大小和活跃寄存器是否引起spill、编译失败或额外VF开销？

## 7. 验收标准

正确性：保持接口语义与原精度阈值，覆盖尾部、容量边界、空域及策略涉及的状态和数值边界。使用正确性对照验证所有受影响路径，不仅验证主路径。

性能：冻结前后源码与二进制，在同设备、同输入、同构建配置下按配对测量协议比较设备Task Duration；先对相同输入域内的多次结果取均值，再按约定跨域聚合，并检查域内回归。

决策：精度、越界、资源或同步检查失败时先修复或回退；没有可信性能收益时保留原路径。组合已有验证不等于其中任一子动作独立有效，单独迁移子动作需要独立验证。

## 检索卡（短卡）

动作：把跨列块不变的行权重提前广播到寄存器，以两条独立FMA部分累加链计算并在列块末合并。
适用：行权重跨列块不变，累加链较长，接口允许浮点重排，权重与部分累加器满足寄存器预算。
限制：严格位一致路径不适用；区分首块清零和后续续加；游标独立；保护尾行；数组不能可靠展开时用固定寄存器。
范围：加权归约、分块聚合、矩阵向量式累加。
检索词：循环交换、权重提升、寄存器驻留、双FMA链、PostUpdate、RegTensor。
机会：权重在各列块反复从UB加载广播，单条FMA依赖链限制并发。
代价：权重和部分累加器增大寄存器占用；末尾合并与额外块调用可能抵消收益。
