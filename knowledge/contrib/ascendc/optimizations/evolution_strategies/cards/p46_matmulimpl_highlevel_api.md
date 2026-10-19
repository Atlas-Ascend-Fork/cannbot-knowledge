---
type: Optimization
title: 'P46: MatmulImpl 高阶矩阵乘 API (MatmulImpl High-Level API)'
description: 用 `matmul::MatmulImpl` 高阶 API + MDL 配置替代手写 L0/L1 缓冲管理，将 ~160 行手写 matmul
  流水线代码压缩到 ~10 行，同时获得框架自动优化的 L1 多缓冲、K 维重排等能力。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P46_matmulimpl_highlevel_api.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P46: MatmulImpl 高阶矩阵乘 API (MatmulImpl High-Level API)

## 核心思想
用 `matmul::MatmulImpl` 高阶 API + MDL 配置替代手写 L0/L1 缓冲管理，将 ~160 行手写 matmul 流水线代码压缩到 ~10 行，同时获得框架自动优化的 L1 多缓冲、K 维重排等能力。

## 代码骨架

// === 改造前（基线）===
```cpp
// 手写 ~160 行: LoadNdGmToNzL1, LoadNzL1ToZzL0A, Mmad, FixpipeNzL0cToNdGm
// 静态 L1_PREFETCH=3, 无动态优化, 无 K 维重排
```

// === 改造后（优化实现）===
```cpp
matmul::MatmulImpl<aT, bT, cT, BiasT, CFG_MDL> mm;
REGIST_MATMUL_OBJ(&tPipe, GetSysWorkSpacePtr(), mm, &mmTilingData_);
mm.SetOrgShape(m, n, k);
mm.SetSingleShape(curSingleM, curSingleN, k);
mm.SetTensorA(xGm[xOffset]);
mm.SetTensorB(weightGm[wOffset]);
mm.IterateAll<true>(yGm[yOffset], false);
```

## 关键修改点

1. 预期收益: 代码量减少 70-80%，框架自动管理 L1/L0 缓冲

## 常见陷阱

⚠️ 依赖框架 MatmulImpl 版本，API 变更需跟进
⚠️ MDL 配置参数（depthA1/depthB1/stepKa/stepKb）需要根据 K 维大小调优
⚠️ 部分极端场景（非标准 layout）可能需要回退到手写

## 代码搜索关键词

```bash
grep -n "tileSize\|ubFactor\|Tiling\|BLOCK_DIM\|SyncAll\|SetFlag\|WaitFlag\|PipeBarrier" op_kernel/*.cpp op_host/*_tiling.cpp
```
