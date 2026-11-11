---
type: Optimization
title: "X49: 两阶段 GEMM 跨核生产/消费切分（N-split stage-split + GM-volatile flag）"
description: "两阶段 GEMM 链若按 M-block 归属或 (mi,ni) tile 分任务，阶段一并行度受 mBlocks 限制（小 M 大 N2 时仅少数核工作）；把 h 的生产与消费拆到不同核（N-split stage-split + GM volatile flag 跨核同步）可提高并行度。"
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

# Strategy X49: 两阶段 GEMM 跨核生产/消费切分（N-split stage-split + GM-volatile flag）

## 核心思路
两阶段 GEMM 链（FFN 的 GEMM1→act→GEMM2、QK^T+PV 等）若按 M-block 归属（X48）或
(mi,ni) tile 分任务，阶段一（GEMM1）的并行度受 mBlocks 限制（小 M 大 N2 时仅少数核
工作，其余空转）。**N-split stage-split**：把"h 的生产"与"h 的消费"拆到不同核——
- **生产者**：K2 切成 P 片，核 0..P-1 各产一片。AIC: GEMM1(x[mi]@W1[:,slice]) →
  AIV: act → h[mi][slice] 写 GM；写完后 AIV 用 **GM volatile flag 广播**
  flag[mi][p]=1（release）。
- **消费者**：所有 G=min(24,nBlocks) 核各领 N2 列块 R_c。AIV 轮询 flag[mi][0..P) 全 1
  （GM volatile 非破坏读，acquire）→ H_READY；AIC: GEMM2(h[mi]@W2[:,R_c])。
- **模式选择**：mode1(N-split) 当且仅当 nBlocks > mBlocks（N-split 并行度 G 高于
  M-split 的 mBlocks），否则 mode0(M-block 归属保底)。G=min(24,nBlocks) 保证每核
  ≥1 输出 tile 规避 tile-less flag 死锁。

## 适用场景
- 两阶段 GEMM 链中阶段一为单核/低并行瓶颈（mBlocks < 核数，如小 M 大 N2 的 FFN /
  QK^T+PV）
- 已有 M-block 归属（X48）但并行度仍受 mBlocks 限制时
- 与带宽路径（baseN 放大 / K 轴错峰）正交可组合

## 实现要点
1. **跨核同步协议（规避竞态）**：生产者写 h（MTE3）后 `PipeBarrier<PIPE_ALL>` 再写
   flag（release）；消费者 MTE2 读 flag（acquire）后才让 AIC 读 h。flag 槽 32B 对齐、
   每 M-block 独立、无需 reset。
2. **flag 缓冲必须零初始化**：用 `at::empty`（垃圾残留）会把垃圾 1 误判为"已就绪"，
   导致 h 未写完就消费 → 必须 `at::zeros` 初始化 workspace。
3. 生产者与消费者的 AIC/AIV 角色分离；P=min(G, K2/128)。
4. 跨 mi 循环串行（produce[mi]→wait→consume[mi]）未做软件流水加深——后续用三缓冲
   思想隐藏。
5. 目标架构无 GM 原子（SetAtomicAdd 不支持），用 GM volatile flag 轮询替代原子计数。

## Trade-off
- flag 轮询有额外 GM 读开销；mode1 仅覆盖 nBlocks>mBlocks 的形态
- 共享 h 的跨核写→读需严格 release/acquire 协议，否则间歇性竞态（可能出现 NaN）

## 验证方法
- **同设备 A/B 对比**：固定设备型号、CANN 版本、输入 shape 与 dtype，优化前后各跑多轮（含 warmup），取 kernel Duration 中位数对比；不跨设备或跨版本混合测量。
- **全精度校验**：用 PyTorch/参考实现逐元素比对，覆盖 mode0/mode1 切换边界与 nBlocks>mBlocks 形态，满足对应 dtype 的 rtol/atol，且无 NaN/Inf。
- **容量审计**：核算 L0C/L1/UB 占用与 h flag/workspace 需求，确认 P 片切分和 32B flag 槽在容量内；检查 16×16 fractal、尾块与 tile-less 死锁边界。
