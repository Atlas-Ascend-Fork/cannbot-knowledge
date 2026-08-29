---
type: Guide
title: 高阶极限打磨
description: 本节在中级性能优化的基础上，介绍Matmul融合算子的高阶极限打磨方法。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/extreme_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 高阶极限打磨

本节在中级性能优化的基础上，介绍Matmul融合算子的高阶极限打磨方法。
> 说明：为更好展示VF融合的性能优化手段，本章节以Matmul+Gelu融合算子作为讲解样例。GELU相比LeakyRelu计算逻辑更复杂，能更充分地体现各类优化手段的效果。
## Matmul高阶优化手段
Case：优化手段：说明
Case 5：MDL + L1Cache优化：手动调整Tiling参数，充分利用L1缓存
Case 6：MDL + L1Cache + L2Cache：分块计算适配L2Cache，提高缓存命中率
Case 7：+ Constants Tiling：Tiling常量化，减少运行时Scalar计算开销
Case 8：+ UnitFlag：细粒度流水同步，MMAD与FIXPIPE流水并行
## Gelu高阶优化手段
Case：优化手段：说明
Case 2：VF融合 + 循环展开：#pragma unroll展开循环，提高指令级并行度
## CV融合：Scenario 2 — CV融合-UB直通
在高阶极限打磨阶段，CV融合层面提供Scenario 2方式（仅Ascend 950PR支持）。AIC侧通过Fixpipe将L0C计算结果直接写入UB，AIV侧无需从GM读取数据，直接在UB上进行GELU计算后将结果写回GM，省去GM中转的读写开销。
> 兼容性说明：A2/A3芯片不支持Fixpipe直写UB，请使用Scenario 1（CV融合-GM中转）方案。
数据流路径：
AIC侧实现：Fixpipe L0C → UB（通过dualDstCtl=0b01开启双目标模式，按M维度拆分给2个AIV）
AIV侧实现：UB → GELU → geluOutUB → GM（无需DataCopy GM→UB）
### 性能数据
以Ascend 950PR芯片数据为例：
- Scenario 2融合后总耗时2573.584μs，相比Scenario 1的2606.91μs进一步减少约33μs
- Scenario 2中aiv_mte2_time仅为0.005μs，相比Scenario 1的57.145μs几乎降为零
详细内容请参见Matmul+Gelu高阶极限打磨。

<!-- cannbot:related:start -->
## 相关

- [中级性能优化](intermediate_optimization.md)（`related`）：本节在中级性能优化的基础上，介绍Matmul融合算子的高阶极限打磨方法。；本节在入门功能落地的基础上，介绍Matmul融合算子的中级性能优化方法。。高阶 Matmul 融合优化明确承接中级优化，后者提供前一阶段的实现基线。
<!-- cannbot:related:end -->
