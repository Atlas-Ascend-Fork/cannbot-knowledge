---
type: Optimization
title: 'R2: 寄存器复用'
description: 通过布尔代数简化、指令重排和原地复用减少 RegTensor 使用量，避免超过 32 个限制导致的 spill/fill。
tags:
- task.optimization
- topic.compute.composite
status: deprecated
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/R2_register_reuse.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-13T00:00:00Z'
platforms:
- '950'
---

# R2: 寄存器复用

> ⚠️ **已废弃**：使用虚构 RegTensor API；寄存器分配由编译器管理，不是可手工施加的 kernel 优化策略，仅作方向留档。**去向**：无直接继任卡，仅留档参考。


## 核心思想
通过布尔代数简化、指令重排和原地复用减少 RegTensor 使用量，避免超过 32 个限制导致的 spill/fill。

## 代码骨架

// === 改造后（优化实现）===
```cpp
// Baseline: 5 个 RegTensor
RegTensor<float> a, b, c, d, result;
Add(c, a, b, mask);
Mul(d, c, a, mask);
Add(result, d, b, mask);

// Evolved: 3 个 RegTensor
RegTensor<float> a, b, tmp;
Add(tmp, a, b, mask);
Mul(tmp, tmp, a, mask);   // 原地复用 tmp
Add(tmp, tmp, b, mask);   // 继续复用
```

## 关键修改点

1. 预期收益: **: RegTensor 从 5 减少到 3
**Trade-off**: tmp 的依赖链变长，可能影响双发射

## 常见陷阱

⚠️ 收益**: 消除 spill/fill 指令，性能提升 10-30%
⚠️ 风险**: 过度复用可能引入数据依赖，阻碍双发射
⚠️ 复杂度**: 需仔细分析寄存器生命周期
