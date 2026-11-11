---
type: Optimization
title: "X32: fp32 投影 GEMM 的精度安全替代与真实瓶颈（MTE2-bound 修正）"
description: "fp32 投影 GEMM 可能主导 GQA prefill 耗时，但 profiling 若显示 GM→L1 搬运饱和，则它实际是 MTE2-bound 而非 compute-bound；此时 bf16/fp16 hi/lo 3/4-GEMM 提升的 cube 吞吐不会转化为端到端收益，正确方向是增大搬运块、L1 双缓冲与消除 GM 往返，并受 L0C/L0B 容量约束。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X32: fp32 投影 GEMM 的精度安全替代与真实瓶颈（MTE2-bound 修正）

## 核心发现
fp32 投影 GEMM 在 GQA prefill 中可能成为 dominant 成本，但 **profiling 可能显示它是 MTE2-bound（GM→L1 搬运饱和、cube 空置），而不是 compute-bound**；固定 64x64 块的 GM→L1 搬运常是瓶颈。

**关键负结果**：P128 bf16 hi/lo（attention 精度通过）与 fp16 hi/lo 3-GEMM（投影）虽把 cube 吞吐翻倍，却没有转化为端到端收益——因为投影已内存受限。早期观察到的大 fp32 提升经复核确认是 profiling 采样伪影；复核后 fp16 hi/lo 投影的净收益不显著。

## 仍然成立的结论
1. **精度路径**：P128 bf16 hi/lo 仅能对 attention 过容差；投影近零输出 MERE 超 2^-13。fp16 hi/lo（相对误差约 2^-21，K≤1472 时 MERE≈9e-6）是投影的精度安全替代（如需保精度）。
2. **投影 GEMM L1 双缓冲**：GM→L1 与 mmad 重叠，是 MTE2-bound 的正确方向（隐藏搬运）。
3. **KV padding 消减**：fp32 nChunk 阈值自适应，中型 S 可减少 QK^T/PV 冗余列。

## 修正后的优化方向
投影 GEMM 若为 MTE2-bound，正确杠杆是内存访问而非 cube 精度：
- 增大投影 GEMM 的搬运块（64x64→更大 tile），减少 undersize transfer
- L1 双缓冲/预取隐藏 GM→L1 延迟
- 消除 split/投影的 GM 往返（pack+split 融合，但仅小/中 shape 有效）

## 边界（否定项）
- **pack+split 全 GM 融合在大 fp32 shape 不可行**（反而变慢，已回退）
- **attention K/V 双缓冲无收益**（真实瓶颈是 AIC/AIV workspace GM 往返）
- **fp16 hi/lo 投影单维度无净收益**（投影 MTE2-bound，cube 吞吐翻倍被内存瓶颈吞没）
- L0C/L0B 须按 max(nChunk, dimPad) 分配防越界（dimPad>nChunk 时会越界写坏相邻输出）

## 验证方法
- **同设备 A/B**：固定输入与 tiling，对比开启/关闭 L1 双缓冲、tile 放大与 hi/lo 路径的 kernel 时间，取多次 warmup 后的中位数；同时用 profiling 核对 MTE2/cube 管道利用率，确认瓶颈确实在搬运侧。
- **全量精度**：覆盖全部 shape 与 dtype，逐元素与 fp32 参考比对；hi/lo 路径重点检查近零输出与大 K 累加。
- **容量审计**：核算 L1/L0C/L0B 占用与 max(nChunk, dimPad) 分配，确认 tile 放大后不越界、双缓冲不超容量。
