---
type: Optimization
title: "X41: singleCoreN 对齐 baseN 倍数（量化 Matmul L0B 填充利用率修复）"
description: "量化 Matmul 大 shape 的 AIC 瓶颈可能不是 MAC，而是 L0B-fill:mad 比与 L2→L1 喂给率；当 singleCoreN 不是 baseN 整数倍时，尾部 masked partial tile 浪费 L0B 填充，将 singleCoreN 对齐到 baseN 倍数可修复。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.quantization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X41: singleCoreN 对齐 baseN 倍数（量化 Matmul L0B 填充利用率修复）

## 核心思路
量化 Matmul 大 shape 的 AIC 瓶颈可能是 **L0B-fill:mad 比 / L2→L1 喂给率**，而非 MAC。当 `MatmulApiTiling` 返回的 `singleCoreN` 不是 `baseN` 的整数倍时，每个 block 的最后一个 base-N tile 是 masked partial（宽度不足 baseN），浪费 L0B 填充带宽。把 `singleCoreN` **round-up 到最近的 baseN 倍数**，使每个 block 由完整 base-N tile 组成，L0B 利用率提升，AIC 时间下降。

## 适用场景
- int8/int4 量化 Matmul（Matmul<> 高层 API + MatmulApiTiling），Cube 累加 int32
- 大 M×N shape 且 `singleCoreN % baseN != 0`（N 落在 baseN 间隔中间）
- 评估口径：Cube mm 主导的 shape（epilogue 占比较小），以 kernel Duration 衡量
- 与 baseM 扩升策略正交：本策略聚焦 singleCoreN 对齐，baseM 扩升是独立杠杆

## 实现要点
1. 在 `GetTiling + 多核 shrink 循环`之后新增对齐逻辑：`singleCoreN = ceil(singleCoreN / baseN) * baseN`；若对齐后 `totalBlock < aicCoreNum`（核数不足），回退到 `baseN` 本身以保住核心网格。
2. **不改 singleCoreM**：避免触发 `singleM < baseM` 的 AIC 崩溃（API 可能返回小于 baseM 的 singleCoreM，不强改）。
3. **对齐过头会变差**：把 singleCoreN 扩到两倍对齐会使 block 过大、block 数减半，破坏 AIC 负载均衡；只对齐到最小 ≥ singleCoreN 的 baseN 倍数，勿过度。
4. SetBufferSpace 对 deep-K shape 无效（depthA1 天然封顶），不做。

## 验证方法
- **同设备 A/B 对比**：固定设备型号、CANN 版本、输入 shape 与 dtype，优化前后各跑多轮（含 warmup），取 kernel Duration 中位数对比；不跨设备或跨版本混合测量。
- **全精度校验**：用 PyTorch/参考实现逐元素比对，覆盖 int8/int4 输入与边界 N，满足对应 dtype 的 rtol/atol，且无 NaN/Inf。
- **容量审计**：核算 L0C/L1/UB 占用与多缓冲需求，确认对齐后的 singleCoreN/baseN tile 在容量内；检查 32B 对齐、16×16 fractal 与尾块处理。
