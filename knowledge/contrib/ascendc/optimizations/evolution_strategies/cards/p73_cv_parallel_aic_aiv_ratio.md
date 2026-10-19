---
type: Optimization
title: 'P73: CV 并行 AIC:AIV 比例与多 Workspace 流水 (CV Parallel AIC:AIV Ratio & Multi-Workspace
  Pipeline)'
description: GroupedMatmul 等 Cube+Vector 融合算子中，当 Vector 计算为主要瓶颈时，可将 AIC:AIV 启动比例从默认
  1:1 调整为 1:2，让更多 AIV 核分担 Vector 计算。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.mixture_of_experts
- topic.implementation.tiling
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P73_cv_parallel_aic_aiv_ratio.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P73: CV 并行 AIC:AIV 比例与多 Workspace 流水 (CV Parallel AIC:AIV Ratio & Multi-Workspace Pipeline)

## 核心思想
GroupedMatmul 等 Cube+Vector 融合算子中，当 Vector 计算为主要瓶颈时，可将 AIC:AIV 启动比例从默认 1:1 调整为 1:2，让更多 AIV 核分担 Vector 计算。同时，Cube 与 Vector 之间通过 workspace 传递数据存在依赖等待；默认 2 份 workspace 的 pingpong 方案仍有互等间隙，扩展到 4 份 workspace 可进一步消除 Cube-Vector 流水气泡。最后，Vector 侧开启 double buffer 进一步提升搬运与计算重叠度。

## 代码骨架

// === 改造后（优化实现）===
```cpp
// Tiling 侧：设置 AIC:AIV 比例为 1:2
// 通过 SetAicAivRatio 或在 kernel launch 配置中设置 mixMode
// 使得每个 AIC 核对应 2 个 AIV 核处理 Vector 后处理
optiling::MatmulConfigParams matmulConfigParams;
matmulConfigParams.aicAivRatio = {1, 2};  // AIC:AIV = 1:2
cubeTiling.SetMatmulConfigParams(matmulConfigParams);

// Kernel 侧：AIV 根据 subBlockIdx 分配工作
uint32_t aivIdx = GetSubBlockIdx();  // 0 或 1
uint32_t aivNum = GetSubBlockNum();  // 2
// 按 aivIdx 将 Vector 后处理工作量均分到 2 个 AIV 核
uint32_t vecStart = aivIdx * totalVecWork / aivNum;
uint32_t vecEnd = (aivIdx + 1) * totalVecWork / aivNum;
```

## 关键修改点

1. 预期收益: 总耗时从 218.1us 降至 154.2us（提升 29.3%），Cube 计算间等待明显减小

## 常见陷阱

⚠️ 1:2 AIC:AIV 比例减少了可用 AIC 核数，Cube 吞吐降低
⚠️ 4 份 workspace 需要 4 倍 GM workspace 空间
⚠️ 仅适用于 MIX 场景的 Cube+Vector 融合算子

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|SyncAll\|PipeBarrier\|ExecuteTask\|PRELOAD\|tileSize" op_kernel/*.cpp op_host/*_tiling.cpp
```
