---
type: Optimization
title: 'P140: MLA（kvHeads=1）的 M-tile 放大到 qHeads（UB/L0 自适应）'
description: FA 里单个 Cube GEMM 的 M 维上限 = **共享同一份 K/V 的查询行数**。
tags:
- task.optimization
- topic.attention
- topic.programming_model.execution_unit.cube
- topic.programming_model.execution_unit.scalar
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P140_mla_large_m_tile.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P140: MLA（kvHeads=1）的 M-tile 放大到 qHeads（UB/L0 自适应）

## 核心思想

FA 里单个 Cube GEMM 的 M 维上限 = **共享同一份 K/V 的查询行数**。GQA 只有 groupSize = qHeads/kvHeads（小，4~16）→ M-tile 天生小、Cube MAC 利用率低；**MLA（kvHeads=1）则共享行数 = qHeads（128~256）**，M-tile 可放大一个数量级（kCubeMaxM 64→128），QK^T/PV 一次 mmad 吃满更多 Cube。放大受 UB（Q compact + score/prob 缓冲）与 L0（见 P138）约束，按运行时可驻留的 `mTileCap` 自适应。

## 代码骨架

```cpp
// host tiling：kvHeads==1（MLA）时 M-tile 可到 qHeads
const int64_t sharedRows = qHeads / kvHeads;          // GQA=groupSize, MLA=qHeads
int64_t mTile = sharedRows < kCubeMaxM ? sharedRows : kCubeMaxM;
// 受 UB/L0 约束再降（配合 P138 的 L0 查询）
while (!FitsUB(mTile) || !FitsL0(mTile)) mTile /= 2;
```

## 关键修改点

1. **M-tile 的上限是"共享 K/V 的查询行数"**：GQA 别硬拉 M（拉不动且没用）；MLA 别写死小 M（浪费 Cube）。按 `qHeads/kvHeads` 定 M-tile 上界。
2. **约束自适应**：放大到 UB（Q/score/prob 缓冲）与 L0（见 P138）都容纳的最大值；`mTileCap` 运行时计算，不写死。
3. **识别信号**：kvHeads=1 的 MLA case（长序列 Dk512/576）明显慢于 GQA——优先查 M-tile 是否被小值封顶。

## 实测验证

- SparseFlashAttention MLA case 9/11/13 服务端各 -48%（case9 1018→523μs），MLA 组整体 -33%~-49%，全部 20 case 零回退；`kCubeMaxM` 64→128 + `mTileCap` 自适应。
