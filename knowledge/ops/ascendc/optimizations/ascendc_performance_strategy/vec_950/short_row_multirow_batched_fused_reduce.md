---
type: Optimization
title: 短行归约的多行合批融合扫描
description: 把行宽不足一个行内展开宽度的独立行归约归一化，按固定行数成组合批，每行各持 max/sum 累加器交错推进，组末统一屏障，余行回落单行路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/short-row-multirow-batched-fused-reduce.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "short-row-multirow-batched-fused-reduce",
  "name": "短行归约的多行合批融合扫描",
  "classification": "validated_strategy",
  "slug": "short-row-multirow-batched-fused-reduce",
  "generality": "dataflow_pattern",
  "feature_signature": {
    "pattern": "short-row-multirow-batched-fused-reduce"
  },
  "verification": {
    "status": "validated_with_preconditions",
    "attribution": "单一输入域实测该机制带来数倍级端到端加速且全量精度通过；收益随行宽、组大小与寄存器预算变化，迁移后必须重新配对测量。",
    "migration_required": true
  }
}
-->

# 性能优化策略：短行归约的多行合批融合扫描

> 单一优化点：当每行有效元素数不足一个行内展开宽度时，把多行合并进同一个 VF，用按行独立的累加器交错推进归约与归一化，并把屏障/归约/广播按组摊薄，余行回落单行路径。

## 1. 原理

逐行归约链通常在一行内做多路展开来隐藏依赖延迟。若每行有效元素数只有一两个向量寄存器宽度，行内展开无法形成足够的独立链，阶段间仍是长依赖串行；同时每行一次 VF 调用和一次写后读屏障，把固定开销重复到每一行。

把固定数量的相邻行组成一组：每行各自持有 max 与 sum 的独立累加器，四（或更多）条链在同一循环内交错发射；组内一次完成归约、广播与归一化，屏障、跨 lane 归约和广播只按组支付一次。组内各行仍完全独立，因此不改变行间语义；组末不足整组的余行必须回落原单行路径，避免为凑组而引入越界或额外掩码逻辑。

## 2. 性能问题模式

- 行宽小于约两个向量寄存器宽度，行内多路展开的独立链数量不足。
- 向量管已绑定但发射槽仍有空闲，表现为单行依赖链等待，而不是搬运带宽受限。
- 逐行 VF 调用、逐行写后读屏障或逐行广播在总时间中占可观比例。
- 相邻行之间无依赖，输出区间互不重叠。

## 3. 正确性红线

- 证明组内各行完全独立，写回区间不重叠；任何跨行归约或行间依赖都不适用。
- 尾组与不足整组的余行必须回落单行路径或使用精确尾掩码，不得越界读写。
- 行距按目标对齐粒度向上取整；窄字宽打包存储的掩码必须按实际有效 lane 生成并做成对偶数化处理。
- 独立累加器会改变浮点加法/乘加的结合顺序：只在精度契约允许时采用，严格位一致路径保留原归约组织；纯极值比较在一致比较序下可保持结果不变。
- 组大小受向量寄存器数量与代码体积约束，必须检查工具链展开后的 spill、指令缓存与尾组占比。

## 4. 泛化条件

适用：行间独立、每行有效元素数少于一至两个向量寄存器宽度、逐行调用与屏障开销显著的行归约/归一化融合链；寄存器预算允许同时驻留多行累加器与临时量。

不适用或需回退：行宽已足够长（行内展开已能形成独立链）、行间存在依赖、搬运带宽主导、寄存器压力导致 spill 或并行组数下降、尾组比例过高、或浮点重排不被精度契约允许。

## 5. 实施步骤

1. 先确认瓶颈是短行串行链与逐行固定开销，而不是 MTE2/MTE3 带宽。
2. 选择组大小（常见为 2 的幂且能整除或覆盖多数行），按行分配独立累加器，其余临时寄存器复用。
3. 组内按阶段交错推进：先并行求各路 max，再并行求 exp/累加 sum，最后并行归一化并写回。
4. 补齐尾组掩码、余行回落、填充区无效值处理与写回掩码。
5. 检查生成代码的寄存器占用与 spill；收益不可信时减小组大小或恢复单行路径。

## 6. LLM 前置问题

- 行是否真正独立，组内写回是否会重叠？
- 每行有效长度与向量宽度之比是多少，行内展开是否已经足够？
- 组内同时驻留的累加器与临时量是否超出寄存器预算并产生 spill？
- 尾组和余行如何回落，填充区无效值是否可能污染归约？
- 浮点累加的重排是否落在精度阈值内？

## 7. 验收标准

正确性：保持原接口、精度阈值与输出布局，覆盖尾组、余行、空域、极端值与所有受影响分支；先验证语义与合法访问，再判断收益。不得为凑组放宽精度阈值。

性能：冻结前后源码与二进制，同设备、同输入、同工具链，按配对测量协议比较设备 Task Duration；每个输入域先取均值，再按约定跨域聚合，并记录域内回退与剔除补测。

决策：出现越界、同步、精度失败或没有可信收益时修复或回退；组合验证不得推出任何子动作独立有效。

## 8. 与相邻策略的边界

与 [dual-row-interleaved-sweep](dual_row_interleaved_sweep.md) 不同：后者面向行宽足够长、单行链由 loop-carried 累加器串行化的场景，用两行交错提升发射密度；本策略的成立前提是行宽不足一个行内展开宽度，行内独立链无法形成，重点在合并多行与摊薄逐行固定开销，两者可评估但不得互相外推。

与 [independent-row-lane-fused-pipeline](independent_row_lane_fused_pipeline.md) 不同：后者把一行映射到一个 lane 并做跨行组级流水；本策略保持每行独立的向量内归约，不改变行到 lane 的映射。

与 [batched-sync-amortization](batched_sync_amortization.md) 不同：后者摊销的是多个工作单元之间的同步提交；本策略摊销的是同一融合链内逐行归一化与屏障的固定成本。

与 [independent-maximum-accumulator-chains](independent_maximum_accumulator_chains.md) 不同：后者在单行内部拆分多路累加链；本策略的并行维度是行，行内仍为单链。

## 检索卡（短卡）

动作：把行宽不足一个行内展开宽度的独立行归约归一化，按固定行数成组合批，每行各持 max/sum 累加器交错推进，组末统一屏障，余行回落单行路径。
适用：行间独立、每行有效元素数少于一至两个向量宽度、逐行调用与屏障开销显著的行归约融合链。
限制：须证明填充/尾组掩码与越界安全；组内寄存器预算与 spill 须实测；余行必须回落；浮点累加分组重排须在精度契约内。
范围：向量类行归约与归一化融合链。
检索词：多行合批、独立累加器、LocalMemBar、屏障摊薄、短行、尾组掩码、寄存器压力、行归约
机会：行宽不足时行内多路展开失效，单行链与逐行屏障使向量发射槽空闲。
代价：组越大寄存器与代码体积越高并可能 spill；搬运主导时收益消失。
