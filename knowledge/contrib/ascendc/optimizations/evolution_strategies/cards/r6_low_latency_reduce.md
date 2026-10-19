---
type: Optimization
title: 'R6: 低延迟归约'
description: 选择最优的归约指令组合，减少 Reduce 类操作的延迟。
tags:
- task.optimization
- topic.compute.composite
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p68_low_latency_reduction
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/R6_low_latency_reduce.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-13T00:00:00Z'
platforms:
- '950'
---

# R6: 低延迟归约

> ⚠️ **已废弃**：内容被 P68（Low-Latency Reduction Instruction Combination）完全覆盖，零引用。**去向**：[P68: Low-Latency Reduction](p68_low_latency_reduction.md)。


## 核心思想
选择最优的归约指令组合，减少 Reduce 类操作的延迟。

## 代码骨架

// === 改造后（优化实现）===
```cpp
// Baseline: 单次 WholeReduceSum（高延迟）

// Evolved: 先按 VL 粒度累加，再全局归约
RegTensor<float> accReg;
MaskReg fullMask = CreateMask<float, MaskPattern::ALL>();
Duplicate(accReg, 0.0f);

for (uint16_t i = 0; i < repTimes; ++i) {
    MaskReg mask = UpdateMask<float>(count);
    LoadAlign(srcReg, srcAddr + i * oneRepSize);
    Add(accReg, accReg, srcReg, mask);  // VL 粒度累加
}

// 最终归约: VL → 标量
StoreAlign(workAddr, accReg, fullMask);
// 在 VF 外部用高阶 API 完成最终归约
```

## 常见陷阱

⚠️ 收益**: 归约延迟降低 2-3x
⚠️ 风险**: 需要额外 RegTensor 做累加器
⚠️ 复杂度**: 中等
