---
type: Optimization
title: "X38: GM-Workspace-Ring KV-tile 宽度缩放 + Host 批量权重打包"
description: "FA 算子若采用 GM workspace ring 队列而非 L1 常驻，每 KV tile 会产生固定次数的 GM 往返、跨核握手与标量开销；放大 KV tile 宽度可直接减半往返次数并增大 cube GEMM 尺寸。融合 QKV/out 投影且 heads 多时，host 侧 per-head 权重打包可批量化为 cat + pad + reshape + 单次 strided copy。"
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

# Strategy X38: GM-Workspace-Ring KV-tile 宽度缩放 + Host 批量权重打包

## 核心思路
FA 算子若采用 **GM workspace ring 队列**（AIC 写 S/P/O → GM → AIV 读）而非 L1 常驻，则每 KV tile 产生固定次数的 GM 往返 + 跨核握手 + 标量开销（此时标量/流水开销占比高，cube MAC 占比低）。此时放大 KV tile 宽度（kvN）不是为了让 L1 常驻，而是**直接减半 GM ring 往返次数**、翻倍 MM1/MM2 的 cube GEMM 尺寸。同时，融合 QKV/out 投影算子的 host 侧 per-head 权重打包（多次 `narrow().copy_()`）构成独立 copy-storm，可批量化为 `cat + pad + reshape + 单次 strided copy`。

## 适用场景
- FA 算子使用 GM workspace ring 握手（AIC↔AIV 经 GM 中转 S/P/O），每 KV tile 固定握手开销主导，而非带宽或 cube 吞吐
- 融合投影 GEMM 且 heads 数多（per-head copy 次数 > 12），host 侧权重打包成为墙钟拖累
- 硬件：Ascend MIX AIC/AIV 架构
- **边界**：不适用于已走 L1 常驻（P53/P18）的 FA 核心，也不适用于 launch-bound 极小 shape 或 heads 很少的轻量场景

## 实现要点
- **kvN 自适应**：新增 tiling 字段 `kvN`。seq<=64 用 64（避免单宽 tile 的 2x 尾块浪费）；seq>64 用 128。所有 workspace 槽/buffer 仍按 128 max 分配，仅 ring slot stride、MM n/k、fixpipe width、softmax srcK、mask、causal 对角索引（`t = bx*BLOCK_M/kvN`）改为运行时 kvN。
- **sPad 对齐 kvN**：放大 tile 后必须 `sPad = align_up(seq, kvN)`（原 64），否则末 KV tile 越界读 mPad（NaN 根因）。
- **host 批量打包**：heads 多时 `cat` 各 head 权重块 → `constant_pad_nd` 补齐 dhPad → `reshape` → 单次 strided copy；heads 少时保留逐 head copy（constant_pad_nd 有固定开销，小 shape 反而拖累）。输出张量用 `at::empty`（kernel 全量覆盖，padded 行被 mask 丢弃，未初始化安全）。
- **收益来源**：KV tile 数减半 → GM ring 往返/握手减半 + cube GEMM 翻倍；host 打包从 O(heads) 次 launch 降到 O(1)。
- **坑点**：kvN 放大需 seq 足够大，使“往返减半”收益超过尾块 padding 与更大 cube 的固定开销；host 打包 fixed-cost 决定其只在 per-head copy 次数多、单次 copy 窄（< 32B）时回本。

## 验证方法
- **同设备 A/B**：固定 seq/dtype/heads 分布，对比不同 kvN 与 host 打包方式的 kernel 时间，取多次 warmup 后的中位数；同时检查 GM ring 往返次数与跨核握手次数。
- **全量精度**：覆盖全部 shape、短 seq 与末 KV tile、causal/非 causal；逐元素与参考 FA 比对，重点检查 sPad 放大后的越界读与 mask 行。
- **容量审计**：核算 workspace 槽按 128 max 分配、ring slot stride 与 L1/UB 占用，确认 kvN 放大后不越界且未初始化输出行均被 mask 丢弃。
