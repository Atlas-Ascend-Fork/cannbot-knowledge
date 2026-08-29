---
type: API
title: ProgrammingModel
description: SIMD与SIMT混合编程支持根据算子特征精细化映射，规则计算用SIMD获得高吞吐，不规则计算用SIMT缓解发散。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/programming_model.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 编程模型

SIMD 与 SIMT 混合编程支持根据算子特征精细化映射：规则逐元素计算用 SIMD 获得高吞吐，不规则或分支计算用 SIMT 缓解发散。同一算子可同时利用两者优势。

线程架构采用分层结构：Grid > Thread Block（最大 2048 线程）> Warp（32 线程）> Thread。Grid 中线程块总数不超过 65535，gridDim 为一维（y、z 必须为 1）。通过 asc_vf_call 调用 SIMT VF 时需显式指定 Thread Block 维度。线程索引：一维 idx = blockIdx.x * blockDim.x + threadIdx.x。

Warp 是基本调度和执行单位，含 32 线程执行相同指令。分支发散（Warp Divergence）时硬件串行执行各分支降低效率，线程数建议设为 32 的整数倍。

UB（Unified Buffer）为线程块内共享内存，总大小 256KB，从低到高依次为静态内存、动态内存、预留空间（8KB）、Data Cache（最小 32KB，最大 128KB）。DataCache = 256KB - 静态 - 动态 - 8KB，小于 32KB 会报错。动态内存可通过 extern 数组或 LocalMemAllocator::Alloc 申请，两者不可同时使用。
