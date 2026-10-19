---
type: Optimization
title: "投影 GEMM exact-N 编译期 da 分发消除零填充列计算 + QKV 三面板共享单次 A-chunk 加载"
description: "融合 attention 的 QKV 投影 GEMM 中，每 (b,h,mb) task 对同一 x A-chunk 做三次独立K-loop(Q/K/V 各一次重读 GM)，且 cube N 维被固定在 128 列模板宽度，而实际 head 宽度da(=AlignUp(D/H,16)) 只有 32.…"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# X73: 投影 GEMM exact-N + QKV 三面板共享单次 A-chunk 加载

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X73
> title: "投影 GEMM exact-N 编译期 da 分发消除零填充列计算 + QKV 三面板共享单次 A-chunk 加载"
> origin: discovered
> discovered_round: 1
> discovered_from: "27_FlashAttention evolution, round_1/parallel_2 (x0, open_exploration)"
> base_speedup: "0.582x -> 0.698x geomean vs PyTorch (+20%; case42 K1 1218us->519us, aic_mac busy 636us->277us; 大 case case48 0.834->1.072, case45 0.806->1.193, 50/50 精度 bit-identical fp32 core)"
> confidence: single_op
> status: active
> op_families: [attention, flash_attention, mha, gqa, matmul]
> bottlenecks: [no_overlap, compute_bound, mte2_stall]
> tags: [exact-n, zero-padding-elimination, compile-time-dispatch, qkv-panel-fusion, a-chunk-reuse, projection-gemm, cube-width, 910b2c, fp32-core]
> strategy_ids: [X33, P1, P5]
> ```

## 核心思路
融合 attention 的 QKV 投影 GEMM 中，每 (b,h,mb) task 对同一 x A-chunk 做三次独立
K-loop(Q/K/V 各一次重读 GM)，且 cube N 维被固定在 128 列模板宽度，而实际 head 宽度
da(=AlignUp(D/H,16)) 只有 32..80 -> 列 [da,128) 是零填充并被计算+丢弃，cube 浪费 2-4x。
两项结构性消除：
1. **QKV 面板融合单 A-chunk**：一个 task 内把 Q/K/V 三个 gemm_v0 累加器并排，x A-chunk
   从 GM 只取一次即被三个投影权重消费（L0C 三块独立 fp32 区，3*da*128*4 <= 128KB）。
2. **exact-N 编译期分发**：gemm N = 真实 head 宽度 da，用编译期 dispatch over
   da ∈ {16,32,48,64,80} 消除零填充列计算（其它 da 回退 padded-128 模板）。
输出布局 [B,H,S,da] 不变 -> K2/K3 字节兼容；fp32 core 数值 bit-identical。

## 适用场景
MHA/GQA/MLA 融合算子的 QKV/out 投影 GEMM：权重按头扩列零填充到 hd_al、da 明显小于
cube 模板 N(128) 的算子；或任一投影中同一 A 被多个权重(如 q/k/v)重复消费的算子。

## 实现要点
- 核数上限提到实有 AIC 数（910B2C=24，勿停在 20）。
- da 编译期分发只在 {16,32,48,64,80} 特化；L0C 3 块 fp32 累加器预算 3*da*128*4 字节。
- 剩余杠杆：fused-K1 K-loop 仍未双缓冲（MAC/MTE2 串行，约再 2x）；FA K2 GM workspace
  往返仍是带宽墙（须配合 CV 流水/UB 常驻或 fp16 cube 降 core 宽度）。

## 来源
自动发现于第 1 轮进化，算子 27_FlashAttention，score 0.698x
