---
type: Optimization
title: 'P60: KV NZ 格式优化 (KV NZ Format Optimization)'
description: 将 KV 矩阵从 ND 格式改为 NZ（Channel-first）格式，使数据布局与 Cube 计算的 L0 输入格式一致，消除 MM1/MM2
  阶段的格式转换开销，提升整体性能。
tags:
- task.optimization
- topic.attention
- topic.programming_model.execution_unit.cube
- topic.data_movement.memory_access
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P60_kv_nz_format_optimization.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P60: KV NZ 格式优化 (KV NZ Format Optimization)

## 核心思想
将 KV 矩阵从 ND 格式改为 NZ（Channel-first）格式，使数据布局与 Cube 计算的 L0 输入格式一致，消除 MM1/MM2 阶段的格式转换开销，提升整体性能。

## 代码骨架

// === 改造前（基线）===
```cpp
// 基线：KV 为 ND 格式，需要 nd2nz 转换
LoadDataToL1(kvL1Tensor, kvGm, nd2nzParams);  // 格式转换开销
```

// === 改造后（优化实现）===
```cpp
// KV NZ 格式：[N, D/16, S/16, 16, 16]
// 与 Cube L0B 格式一致，无需 nd2nz 转换

// 原始 ND 格式：需要 DataCopy nd2nz
// LoadB 阶段：DataCopy(nd2nz) → L1 → LoadB → L0B

// NZ 格式优化：直接加载
// LoadB 阶段：DataCopy(连续) → L1 → LoadB → L0B（无转换）

// 性能收益
// 未叠加双页表：250us → 213us
// 叠加双页表：210us → 178us
```

## 关键修改点

1. 预期收益: 消除 KV 的 ND→NZ 格式转换开销，显著提升 MM1/MM2 性能

## 常见陷阱

⚠️ 需要 KV 数据以 NZ 格式存储，增加上游数据准备复杂度
⚠️ 非对齐场景处理复杂
⚠️ 与现有 ND 格式算子不兼容

## 代码搜索关键词

```bash
grep -n "tileSize\|ubFactor\|Tiling\|BLOCK_DIM\|DataCopy\|CopyIn\|CopyOut\|Fixpipe" op_kernel/*.cpp op_host/*_tiling.cpp
```
