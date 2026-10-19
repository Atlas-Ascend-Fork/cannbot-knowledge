---
type: Optimization
title: 'R4: Hardware Loop 规范化'
description: 确保 VF 内的循环满足 Hardware Loop 编码要求，避免退化为 Software Loop。
tags:
- task.optimization
- topic.compute.composite
status: deprecated
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/R4_hw_loop.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-13T00:00:00Z'
platforms:
- '950'
---

# R4: Hardware Loop 规范化

> ⚠️ **已废弃**：内容单薄（uint16_t vs uint32_t 循环计数），与 P67 Counter Mode 重叠，算子查表零引用，仅作方向留档。**去向**：无直接继任卡，仅留档参考。


## 核心思想
确保 VF 内的循环满足 Hardware Loop 编码要求，避免退化为 Software Loop。

## 代码骨架

// === 改造后（优化实现）===
```cpp
// ❌ Software Loop: uint32_t 类型
for (uint32_t i = 0; i < bound; i++) { ... }

// ✅ Hardware Loop: uint16_t 类型
for (uint16_t i = 0; i < (uint16_t)bound; i++) { ... }
```

## 常见陷阱

⚠️ 收益**: Hardware Loop 比 Software Loop 快 2-5x（减少分支预测开销）
⚠️ 风险**: 代码可读性略降（for(1) 替代 if）
⚠️ 复杂度**: 低（机械替换）
