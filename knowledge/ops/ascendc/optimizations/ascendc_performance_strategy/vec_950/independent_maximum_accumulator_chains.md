---
type: Optimization
title: 纯极值归约的多路独立累加链
description: 把纯极值归约单依赖链拆为多路独立部分状态，扫描末归并并单独处理尾部。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/independent-maximum-accumulator-chains.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "independent-maximum-accumulator-chains",
  "name": "纯极值归约的多路独立累加链",
  "classification": "validated_strategy",
  "slug": "independent-maximum-accumulator-chains",
  "generality": "dataflow_pattern",
  "feature_signature": {
    "pattern": "independent-maximum-accumulator-chains"
  },
  "verification": {
    "status": "validated_with_preconditions",
    "attribution": "纯整数键Max路径已有独立对照；不能外推至复杂值索引更新或任意浮点重排。",
    "migration_required": true
  }
}
-->

# 性能优化策略：纯极值归约的多路独立累加链

> 单一优化点：把纯极值归约的单累加器依赖链拆成有界的多路独立部分极值，扫描末合并并显式处理尾部。

## 1. 原理

当Load后的Max必须等待同一累加器的上次结果时，循环可能受依赖延迟限制。将位置按固定余数分配给少量累加器，使相邻更新落在不同依赖链，增加可同时发射的独立工作；扫描末按同一比较规则归并。

纯整数Max在一致比较序下具有结合性，可保持最终键逐位相同。该论证不自动覆盖带索引Compare/Select链、NaN传播或其他浮点运算。独立链数是资源与延迟之间的选择，不应把某个展开数当作通用常数。

## 2. 性能问题模式

- 输入已在片上，单个最大值寄存器的读后写依赖仍形成等待气泡。
- 指令数量有限而发射吞吐未被充分利用。
- 有足够候选与可用寄存器，却没有独立部分归约。

## 3. 正确性红线

- 证明当前比较序和归并操作具有所需结合性，所有部分状态使用同一有效性约定。
- 保证每个有效候选恰好参与一条链；初始化应为合法幺元，或带独立有效位。
- 非整倍数尾部不得越界读取，也不得遗漏或重复。
- 保持寄存器与代码体积预算；检查工具链展开、寄存器溢出和指令缓存影响。
- 不能将简单Max的收益外推给复杂索引链；存在NaN或位一致约束时另行证明。

## 4. 泛化条件

适用：纯可结合极值归约的依赖链限制吞吐，候选足够多且寄存器预算允许额外部分状态。

不适用或需回退：数据搬运主导、候选太短、比较语义不可结合，或部分归约和末尾合并引起资源及性能回退。

## 5. 实施步骤

1. 确认热点为单状态依赖链，保持布局和比较编码固定。
2. 选择少量独立状态，将扫描元素无重叠地分配给各链。
3. 补齐幺元、无有效值、尾部和末尾归并。
4. 检查生成代码、寄存器及spill，避免只看源级展开。
5. 逐步比较链数与总设备耗时，收益不可信时恢复单链。

## 6. LLM 前置问题

- 比较序是否确实可结合，特殊值如何处理？
- 链数增加后活跃寄存器和代码体积是否仍可控？
- 尾部元素归属与无有效候选状态是否完整？
- 新的独立工作是否真正进入不同依赖链？

## 7. 验收标准

正确性：保持原接口、精度阈值和输出布局，覆盖空域、尾部、容量边界、重复值和所有受影响分支。先验证语义与合法访问，再判断收益；不放宽阈值以迁就新路径。

性能：冻结前后源码和二进制，同设备、同输入、同工具链，依照配对测量协议比较设备Task Duration；每个输入域先取均值，再按约定跨域聚合，保留域内回归和剔除补测记录。迁移到新的资源、布局或数值域必须重新验证。

决策：资源、越界、同步或精度检查失败时修复或回退；没有可信收益时保留原路径。组合验证不能推出任何子动作独立有效。

## 8. 与相邻策略的边界

与[weight-hoist-dual-chain-block-accumulation](weight_hoist_dual_chain_block_accumulation.md)的浮点加权累加重排不同，本策略针对已定义比较序下的纯极值归约；不能直接复用浮点累加的精度论证或展开参数。

## 检索卡（短卡）

动作：把纯极值归约单依赖链拆为多路独立部分状态，扫描末归并并单独处理尾部。
适用：可结合比较的依赖延迟限制吞吐，候选足够多且寄存器有余量。
限制：每项恰好归属一链；幺元或有效位合法；复杂索引链和浮点特殊值需另证。
范围：纯整数键与其它可结合极值归约。
检索词：Max、LoadAlign、ILP、独立累加器、尾部、spill
机会：单状态读后写依赖造成发射气泡。
代价：增加寄存器、代码体积和末尾合并，链数必须实测选择。
