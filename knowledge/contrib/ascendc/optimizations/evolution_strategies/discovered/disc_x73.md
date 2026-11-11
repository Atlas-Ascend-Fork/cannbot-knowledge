---
type: Optimization
title: "投影 GEMM exact-N 编译期 da 分发消除零填充列计算 + QKV 三面板共享单次 A-chunk 加载"
description: "融合 attention 的 QKV 投影 GEMM 中，每个 (b,h,mb) task 对同一 x A-chunk 做三次独立 K-loop（Q/K/V 各重读 GM），且 cube N 维被固定在模板宽度，实际 head 宽度 da(=AlignUp(D/H,16)) 明显小于模板 N，导致零填充列被计算后丢弃。两项结构性消除：QKV 面板共享单次 A-chunk 加载与 exact-N 编译期分发。"
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

# X73: 投影 GEMM exact-N + QKV 三面板共享单次 A-chunk 加载

## 核心思路
融合 attention 的 QKV 投影 GEMM 中，每 (b,h,mb) task 对同一 x A-chunk 做三次独立
K-loop(Q/K/V 各一次重读 GM)，且 cube N 维被固定在 128 列模板宽度，而实际 head 宽度
da(=AlignUp(D/H,16)) 明显小于 128 -> 列 [da,128) 是零填充并被计算+丢弃，cube 算力
被浪费。两项结构性消除：
1. **QKV 面板融合单 A-chunk**：一个 task 内把 Q/K/V 三个 gemm_v0 累加器并排，x A-chunk
   从 GM 只取一次即被三个投影权重消费（L0C 三块独立 fp32 区，3*da*128*4 <= 128KB）。
2. **exact-N 编译期分发**：gemm N = 真实 head 宽度 da，用编译期 dispatch over
   da ∈ {16,32,48,64,80} 消除零填充列计算（其它 da 回退 padded-128 模板）。
输出布局 [B,H,S,da] 不变 -> K2/K3 字节兼容；fp32 core 数值 bit-identical。

## 适用场景
MHA/GQA/MLA 融合算子的 QKV/out 投影 GEMM：权重按头扩列零填充到 hd_al、da 明显小于
cube 模板 N(128) 的算子；或任一投影中同一 A 被多个权重(如 q/k/v)重复消费的算子。

## 实现要点
- 核数上限提到实有 AIC 数（910B2C 为 24，勿硬编码更小的值）。
- da 编译期分发只在 {16,32,48,64,80} 特化；L0C 三块 fp32 累加器预算 3*da*128*4 字节。
- 剩余杠杆：fused-K1 K-loop 仍未双缓冲（MAC/MTE2 串行）；FA K2 GM workspace
  往返仍是带宽墙（须配合 CV 流水/UB 常驻或 fp16 cube 降 core 宽度）。

## 验证方法
- **性能**：在目标设备上对父变体与变体做同一时间窗口的 A/B（正反序至少两轮），
  以绝对时延和配对差值判断，不用跨窗口比值。
- **精度**：跑全量精度用例，逐元素对比参考实现；fp32 core 路径要求逐 bit 一致。
- **容量**：先审计 L0C/L1/UB 预算（含 3*da*128*4 的累加器占用与 workspace），
  确认无越界或静默覆写。
