---
type: API
title: 编程模型
description: SIMT编程模型采用Grid、Thread Block、Warp、Thread分层线程结构，适合控制流复杂和访存模式不规则的算子场景。
tags: [task.lookup, topic.implementation.api_layer.simt_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMT_programming_intro/programming_model.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 编程模型

SIMT 编程适合控制流复杂和访存模式不规则的算子场景，每个线程拥有独立的控制流和地址计算能力，支持原子操作和线程间内存屏障。

线程架构采用分层结构：Grid（线程块网格）> Thread Block（线程块，最大 2048 线程）> Warp（线程束，32 线程）> Thread（线程）。Grid 中线程块总数不超过 65535，各线程块独立执行。内置变量 gridDim、blockDim、blockIdx、threadIdx 用于线程标识。线程索引计算：一维 idx = blockIdx.x * blockDim.x + threadIdx.x。

Warp 是基本调度和执行单位，含 32 个线程执行相同指令。条件分支导致分支发散（Warp Divergence）时硬件串行执行各分支，降低效率。Thread Block 线程数建议设为 32 的整数倍。

UB（Unified Buffer）为线程块内共享内存，总大小 256KB，从低到高依次为静态内存（编译期确定）、动态内存（启动时配置）、预留空间（8KB）、Data Cache（最小 32KB，最大 128KB）。DataCache = min(256KB - 静态 - 动态 - 8KB, 128KB)，小于 32KB 会报错。
