---
type: Optimization
title: "X33: attention workspace-ring 握手延迟 bound 的 Q-tile 放大 + 投影 GEMM group A-reuse"
description: "跨核 AIC↔AIV workspace-ring 流水的 attention 在管道利用率低、耗时高时受握手延迟约束；按任务放大 Q-tile 可减少握手次数，投影 GEMM 在 MTE2-bound 时可用 by-group A-reuse 降低 A 侧 over-read。两者的前提分别是 L0C/L1 容量与瓶颈判定。"
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

# X33: attention workspace-ring 握手延迟 bound 的 Q-tile 放大 + 投影 GEMM group A-reuse

## 核心发现
attention 若采用跨核 AIC↔AIV workspace-ring 流水，可能受**握手延迟**约束（各管道利用率均低，非带宽/计算 bound）。fp32 投影 GEMM 则可能是 **MTE2 (GM→L1) 管道饱和**（cube 空置）。

两个有效杠杆：
1. **attention per-task Q tile 放大**（GQA_BLOCK_Q 32→64→128）：每次放大把 AIC↔AIV workspace-ring 握手次数减半，直接压 attention 的延迟 bound。Q-tile 放大需同步调整 AIV 每任务处理的 HQ-row 组数（GQA_HALF_Q / softmax tile），并处理小 seq 的 AIV padding 浪费（padding-row skip）；配合 PV row-chunked（GQA_PV_CHUNK=64）控制 P 的 L1 缓存宽度。
2. **投影 GEMM by-group A-reuse**（GQA_GEMM_GROUP_BY=6）：每个 task 计算 [64,6] 输出 slab，A tile 每 k-step 只载一次、被 6 列 B 复用，显著降低 A 的 GM over-read。GROUP_BY 上限由 L0C 容量决定（GROUP_BY×BLK×BLK×4B ≤ L0C）；GROUP_BY=8 需 128KB L0C（满容量）时会在设备上 fault，故取 6（96KB）。

## 关键负结果（延续 X32）
- fp16 hi/lo 投影是精度安全替代，非提速手段（MTE2-bound 吞掉 cube 增益）。
- P87 L0 重叠（L1→L0 与 mmad 并发）可能触发 AICore 死锁；P104 块缩小回归；P66 K-batch 放大回归；P92 A-reuse group=2 在网格不足时为中性（GROUP_BY=6 需网格足够大才有效）。
- 投影 GEMM 残余瓶颈常在 B 侧权重搬运，A 侧优化空间有限。

## 适用场景
- attention/FA/GQA 类跨核 workspace-ring 流水 kernel，profiling 显示各管道利用率低但耗时高 → 放大 Q-tile 减少握手次数。
- MTE2-bound 投影/GEMM，A 侧 over-read 严重 → by-group A-reuse。
- **前提**：by-group A-reuse 只在投影 GEMM 是 MTE2-bound（MTE2 利用率高、cube 管道明显空置）时有效；若瓶颈是 cube 计算或输出带宽，GROUP_BY 只会增加 L0C 压力并可能回退。
- 与 X24（AIC_ONLY 纯 cube / AIV_ONLY 纯搬移 kernel）叠加：X24 压 launch 地板，P1 L1 双缓冲压 GM→L1 延迟，三组合是 GQA 投影+attention 的有效配方。

## 实现要点
- Q-tile 放大需同步 AIV 每任务处理的 HQ-row 组数（GQA_HALF_Q / softmax tile），并处理小 seq 的 AIV padding 浪费（padding-row skip）。
- GROUP_BY 上限由 L0C 容量决定（GROUP_BY × BLK × BLK × 4B ≤ L0C），设备 fault 需降级。
- **先判瓶颈再开 A-reuse**：用 profiling 确认 MTE2 利用率高且 cube 管道明显空置；若 cube 已饱和则不要增加 GROUP_BY。
- 与 P92（A-reuse）区分：P92 是 L1 cache 复用（中性），X33 是显式 task 级 group 复用。

## 验证方法
- **同设备 A/B**：固定 shape/dtype，对比不同 Q-tile 与 GROUP_BY 配置的 kernel 时间，取多次 warmup 后的中位数；同时采集各管道利用率，验证瓶颈确在握手/MTE2 侧。
- **全量精度**：覆盖全部 shape、小 seq 与大 seq、causal/非 causal；逐元素与参考实现比对，重点检查 padding-row 与末 KV tile。
- **容量审计**：核算 Q-tile 放大后的 UB/L1 占用、PV chunk 宽度与 GROUP_BY 的 L0C 占用（GROUP_BY×BLK×BLK×4B ≤ L0C），确认无越界且 fault 配置可降级。
