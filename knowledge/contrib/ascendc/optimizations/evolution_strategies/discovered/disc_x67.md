---
type: Optimization
title: "MatmulImpl 中档 M per-(M,N) 三候选网格自适应分发"
description: "MatmulImpl 单一 M-block×full-N 阈值对中档 M 会因 full-N 的 B 矩阵冗余（N 大时每核块数少、无流水隐藏）或 N-split 核数不足（N 小时只用少数核）而失配。改为 host 侧按 (M,N) 枚举三候选网格——A(M-block×full-N) / B(baseN N-split) / C(2D M-block×baseN)——按核数与每核块数对比选最优，kernel 统一读 host 下发的步长，使不同 M/N 规模都能命中最优网格。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.tiling
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X67: MatmulImpl 中档 M per-(M,N) 三候选网格自适应分发

## 核心思路
MatmulImpl 高阶 API 的 GEMM 分发方式（M-block×full-N vs baseN N-split）对核利用有决定性影响，但**单一固定阈值对中档 M 失配**：

- **M-block×full-N**：N 维保持 full，A 跨 N 复用。但 N 很大时每核只需 1 个 M-block（totalBlock 少），full-N 的 B 矩阵冗余读放大，且每核仅 1 块，无流水隐藏。
- **baseN N-split**：N 维按 256 分块跨核。但 N 很小时（例如 direct-path GEMM1 的输出列数很小），只用少量核，多数核空置。
- **2D 网格 (M-block=128 × baseN=256)**：每块恰为 base tile，无 full-N 冗余，24 核均衡分摊——中档 M 的最优解。

host 侧按 (M,N) 枚举三候选网格，按**核数 + 每核块数**对比选最优，把选中的 M-step/N-step 下发给 kernel；kernel 统一读 host 步长遍历，不同规模各自命中最优网格。

## 适用场景
- MatmulImpl 实现的 matmul 系算子，中档 M（数百到数千），N 跨度大（数百到数万）
- GEMM1 输出列数因 path（LoRA/direct）差异导致 N-split 核数波动
- 混合 shape 调用，单一阈值无法同时覆盖 N 小（N-split 欠核）与 N 大（full-N 冗余）的场景

## 实现要点
1. host 枚举三候选：A(M-block×full-N)、B(N-split baseN)、C(2D M-block×baseN)，各算 totalBlock
2. 选核数最多且每核块数≥2 的候选（避免 full-N 每核 1 块无流水隐藏）；核数相同时优先 2D
3. host 回填 M-step/N-step 到 tiling 字段；kernel 读字段统一遍历（full-N M-block 分支 / N-split 分支 / 2D 分支合一）
4. 尾块 curM/curN 越界守卫保留；usedCoreNum 与 kernel tile 网格严格一致
5. 与 P104 互补：P104 只在 totalBlock<aicCoreNum 时缩小 tile，X67 提供 per-shape 网格选择

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），对比父变体与变体；覆盖 M/N 两端及 N 小、N 大的混合 shape，用全量精度门禁确认逐 bit/逐元素一致。
- 网格类改动先审计核数与每核块数（含尾块与 usedCoreNum 一致性）；容量类改动再审计 UB/L1/L0C 预算。
