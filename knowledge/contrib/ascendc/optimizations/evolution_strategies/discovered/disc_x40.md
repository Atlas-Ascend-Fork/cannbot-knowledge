---
type: Optimization
title: "X40: MatmulApiTiling 单核陷阱 + singleN/singleM hint 前置多核化（totalBlock=1 → per-M 自适应 24 blocks）"
description: "小 shape GEMM 用 MatmulApiTiling::GetTiling(TCubeTiling&) 时，API 会为整块能塞进单核的 shape 返回 singleCoreM=M、singleCoreN=N（totalBlock=1），使 GEMM 只跑在 1 个 AIC 核上。修复是在 GetTiling 之前设置 singleN/singleM hint，让 API 自洽重排依赖字段；严禁在 GetTiling 之后手改。"
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

# X40: MatmulApiTiling 单核陷阱 + singleN/singleM hint 前置多核化

## 核心思路
小 shape GEMM 用 `MatmulApiTiling::GetTiling(TCubeTiling&)` 时，API 会为"整块能塞进单核"的 shape 返回 `singleCoreM=M, singleCoreN=N`（`mTotalCnt=nTotalCnt=1` → **totalBlock=1**），即**所有 GEMM 都只跑在 1 个 AIC 核上**（如 24 核只用 1 核），这是小 shape GEMM 算子性能杀手。修复：在调用 `GetTiling` **之前**设置 `tilingApi.singleN = 128`（或 per-M 分段的 singleN/singleM）hint，让 API **自洽地**重排 `singleCoreN/baseN/baseK/stepN/depthA1/depthB1`，得到多 N-block，吃满可用 AIC 核。**关键纪律**：hint 必须在 `GetTiling` 之前设置；严禁在 GetTiling 之后手工缩小 singleCoreM/N（不重算 stepN/depthA1/depthB1/baseK 会导致 AIC trap 507014）。per-M 自适应经验规则：M≤64 → N-split singleN=32；64<M≤128 → singleM=64；M>128 → singleM=M/4 ALIGNED_H=16。

## 实现要点
**Key code change**:
```cpp
// Before: MatmulApiTiling 返回 singleCoreM=M, singleCoreN=N → totalBlock=1（单核 GEMM）
matmul_tiling::MatmulApiTiling tilingApi(*platform);
tilingApi.SetShape(M, N, K);
tilingApi.GetTiling(header.cubeTiling);   // totalBlock = mCnt*nCnt = 1 → 只用 1 AIC 核

// After: GetTiling 前设置 singleN hint → API 自洽重排依赖字段 → 多 N-block 吃满核
matmul_tiling::MatmulApiTiling tilingApi(*platform);
tilingApi.singleN = 128;                    // hint 必须前置
tilingApi.SetShape(M, N, K);
tilingApi.GetTiling(header.cubeTiling);     // singleCoreN=128, baseK=128, depthA1/B1 重算
// totalBlock = ceil(N/128) → 按 N 自动得到多 block
// per-M 自适应：M≤64 nsplit singleN=32；64<M≤128 singleM=64；M>128 singleM=M/4
```

## 适用场景
- **小 shape / 单 tile 可装入单核**的 GEMM（M/N/K 小，API 倾向返回 singleCoreM=M, singleCoreN=N）
- 诊断方法：调试日志打印 tiling 头，或 host 读 `totalBlock` 确认是否 =1 / < aicCoreNum
- 与 P54 launch 融合（M-batching：精度 split GEMM 激活 M 拼接一次 launch）叠加收益最大
- 对计算密集大 shape（totalBlock 本已 ≥ 核数）无显著收益
- 必须保持 tiling 字段自洽性（hint 前置，禁 GetTiling 后手改）

## 验证方法
- **同设备 A/B**：固定 shape 集合与 dtype，对比 hint 前置与默认 GetTiling 的 kernel 时间，取多次 warmup 后的中位数；核对 `totalBlock` 是否达到可用 AIC 核数。
- **全量精度**：覆盖全部 shape，逐元素与参考 matmul 比对；重点验证 per-M 分段边界（M≤64、64<M≤128、M>128）与 totalBlock 不整除的尾块。
- **容量审计**：核算 L0C/L1 占用与 singleCoreM/N、baseN/baseK、stepN/depthA1/depthB1 的自洽性，确认 hint 后无越界且不触发 AIC trap。

## 关联
- X40（关联 P104 多核切分扩展、P2 自适应分块、P54 launch 融合）
