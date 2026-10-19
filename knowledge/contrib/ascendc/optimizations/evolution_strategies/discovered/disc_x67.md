---
type: Optimization
title: "MatmulImpl 中档 M per-(M,N) 三候选网格自适应分发"
description: "MatmulImpl 单一 M-block×full-N 阈值（如 T≥2048）对中档 T 会因 full-N B 矩阵冗余（N 大时每核仅 1 块无流水隐藏）或 N-split 核数不足（N=oc1Pad 小时只用 3-9 核）而失配。改为 host 侧按 (M,N) 枚举三候选网格——A(M-block=128×full-N) / B(baseN N-split) / C(2D M-block×baseN)——按核数与每核块数对比选最优，kernel 统一读 host 下发的步长，实现 mid-T GEMM1 从 3-9 核提到 24 核（MLA Preprocess 0.9931x→1.0206x，+2.8% 突破 1.0x；case14 +12%、case21 +8.2%、case31-48 +2-8%；2D 网格比单一阈值在 case49 多 +7%）。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.tiling
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X67: MatmulImpl 中档 M per-(M,N) 三候选网格自适应分发

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X67
> origin: discovered
> title: MatmulImpl 中档 M per-(M,N) 三候选网格自适应分发
> description: MatmulImpl 单一 M-block×full-N 阈值（如 T≥2048）对中档 T 会因 full-N B 矩阵冗余（N 大时每核仅 1 块无流水隐藏）或 N-split 核数不足（N=oc1Pad 小时只用 3-9 核）而失配。改为 host 侧按 (M,N) 枚举三候选网格——A(M-block=128×full-N) / B(baseN N-split) / C(2D M-block×baseN)——按核数与每核块数对比选最优，kernel 统一读 host 下发的步长，实现 mid-T GEMM1 从 3-9 核提到 24 核（MLA Preprocess 0.9931x→1.0206x，+2.8% 突破 1.0x；case14 +12%、case21 +8.2%、case31-48 +2-8%；2D 网格比单一阈值在 case49 多 +7%）。
> confidence: single_op
> status: active
> op_families: ['matmul']
> bottlenecks: ['tiling_imbalance', 'scalar_loading', 'no_overlap']
> tags: ['matmul', 'multi-core', 'adaptive-grid', '2d-tile', 'mid-shape', 'core-utilization']
> discovered_round: 16
> discovered_from: round_16/parallel_1 (67_MlaPreprocessOperation)
> base_speedup: 0.9931x → 1.0206x (geomean, 50/50 precision pass)
> ```

## 核心思路
MatmulImpl 高阶 API 的 GEMM 分发方式（M-block×full-N vs baseN N-split）对核利用有决定性影响，但**单一固定阈值对中档 M 失配**：

- **M-block×full-N**：N 维保持 full，A 跨 N 复用。但 N 很大时每核只需 1 个 M-block（totalBlock 少），full-N 的 B 冗余读放大（case49 T=1280 实测 +1.13% 回退：B 冗余 216MB，10 核每核仅 1 块，无流水隐藏）。
- **baseN N-split**：N 维按 256 分块跨核。但 N=oc1Pad 很小时（如 direct-path GEMM1 N=576），只用 3-9 核，24 核空置。
- **2D 网格 (M-block=128 × baseN=256)**：每块恰为 base tile，无 full-N 冗余，24 核均衡分摊——中档 M 的最优解。

host 侧按 (M,N) 枚举三候选网格，按**核数 + 每核块数**对比选最优，把选中的 M-step/N-step 下发给 kernel；kernel 统一读 host 步长遍历，大T/小T 各自命中最优网格。

## 适用场景
- MatmulImpl 实现的 matmul 系算子，中档 M（M≈512-8192），N 跨度大（576-24576）
- GEMM1 输出列 N=oc1Pad 因 path（LoRA/direct）差异导致 N-split 核数剧烈波动
- 混合 shape 调用，单一阈值无法同时覆盖 N 小（N-split 欠核）与 N 大（full-N 冗余）的 case

## 实现要点
1. host 枚举三候选：A(M-block×full-N)、B(N-split baseN)、C(2D M-block×baseN)，各算 totalBlock
2. 选核数最多且每核块数≥2 的候选（避免 full-N 每核 1 块无流水隐藏）；核数相同时优先 2D
3. host 回填 M-step/N-step 到 tiling 字段；kernel 读字段统一遍历（大T M-block 分支 / N-split 分支 / 2D 分支合一）
4. 尾块 curM/curN 越界守卫保留；usedCoreNum 与 kernel tile 网格严格一致
5. 与 P104 互补：P104 只在 totalBlock<aicCoreNum 时缩小 tile，X67 提供 per-shape 网格选择

## 来源
自动发现于第 16 轮进化，算子 67_MlaPreprocessOperation（MLA 预处理 GEMM1，910B2C，bf16/fp16），speedup 0.9931x → 1.0206x（+2.8%，突破 1.0x 目标），50/50 精度全通过。
