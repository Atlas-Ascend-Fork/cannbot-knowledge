---
type: Optimization
title: "X48: 链式 GEMM M-block 归属调度（第一阶段输出复用）"
description: "两阶段 GEMM 链若按 (mi, ni) 输出 tile 划分任务，第一阶段会被重复计算 nBlocks 次；按 M-block 归属调度，让每个 M-block 的第一阶段只算一次，中间结果在核 group 内复用，可消除这一冗余。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.normalization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X48: 链式 GEMM M-block 归属调度（第一阶段输出复用）

## 核心思路
两阶段 GEMM 链（FFN 的 GEMM1→激活→GEMM2、QK^T→softmax→PV、SwiGLU 等）在朴素实现中，
若按 `(mi, ni)` 输出 tile 划分任务，每个 tile 独立执行完整串行链，则 **GEMM1（第一阶段）
会被重复计算 nBlocks 次**（同一 M-block 的每个 N 输出 tile 各算一遍）。nBlocks 越大，
冗余越严重。

修复：**M-block 归属调度**——把 mBlocks 个 M-block round-robin 分给各核 group，每个
group 独占其 M-block 的全部 nBlocks 个 N 输出 tile，**GEMM1 每个 M-block 只算一次**，
中间结果（激活后的 h）在 group 内复用，GEMM2 循环遍历本 group 的 ni tile。

## 适用场景
- 两阶段 GEMM 链：FFN (GEMM1→act→GEMM2)、QK^T+PV、SwiGLU、MoE FFN 等，第一阶段输出
  被第二阶段多个 N-tile 消费
- 大 N1（hidden/输出维大，nBlocks≥16）时收益最大（冗余倍数 = nBlocks）
- 小 M（mBlocks < 核数）时并行度受限，需配合其他多核手段（见 trade-off）

## 实现要点
1. `BlockScheduler` 改写为 M-block 归属：`mBlocks` round-robin 分给 `numCores` 个 group，
   每 group 处理 `(mBlock, 全部 ni)` 的完整列块
2. `ProcessCube(mi)`：GEMM1(全 N1) 每 M-block 只算一次 → workspace；`ProcessVec(mi)`：
   激活只算一次 → h；GEMM2/epilogue 循环遍历本 group 的 ni
3. `usedCoreNum = min(核数, mBlocks)`（并行度 = M-block 数而非输出 tile 数）
4. 与 host 固定开销消除策略正交可叠加；glu 变体注意 gate/up 双段读取逻辑
5. 更强但未攻克的变体：N-split 全核摊薄 B 读（共享 h 的跨核写→读存在间歇性竞态，
   SyncAll/PipeBarrier 均无法消除，需 GM-volatile flag 协议重构跨核同步）

## Trade-off
- 并行度 ≤ mBlocks，mBlocks < 核数时核利用不足（小 shape 内存带宽受限，可能轻微回退）
- 消除 GEMM1 nBlocks 倍冗余，但未消除第一阶段输出经 GM workspace 的中间往返
  （进一步优化见片上链式策略）

## 验证方法
- **同设备 A/B 对比**：固定设备型号、CANN 版本、输入 shape 与 dtype，优化前后各跑多轮（含 warmup），取 kernel Duration 中位数对比；不跨设备或跨版本混合测量。
- **全精度校验**：用 PyTorch/参考实现逐元素比对，覆盖 nBlocks/mBlocks 边界与大 N1 形态，满足对应 dtype 的 rtol/atol，且无 NaN/Inf。
- **容量审计**：核算 L0C/L1/UB 占用与 workspace 中间结果需求，确认 M-block 归属下的 h 复用不超容量；检查 32B 对齐、16×16 fractal 与 output tile 尾块。
