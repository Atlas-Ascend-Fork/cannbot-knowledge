---
type: API
title: SimdSimtHybridProgrammingIntro
description: SIMD与SIMT混合编程简介，包含编程模型、扩展语法和API列表导航。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/SIMD_SIMT_hybrid_programming_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# SimdSimtHybridProgrammingIntro

SIMD 与 SIMT 混合编程允许在同一算子中结合两种编程范式：SIMD 侧重 Vector/Cube 上的数据并行计算，SIMT 侧重 Thread Block 内的线程级并行。混合编程用于充分发挥硬件不同计算单元的吞吐能力。
本入口提供三部分导航：编程模型说明混合编程的执行模型与调度方式；扩展语法介绍混合编程所需的函数限定符与变量地址空间标注；API 列表汇总可用的混合编程接口。
使用前需确认目标硬件支持 SIMD 与 SIMT 混合执行，并遵循扩展语法对函数与变量的标注约束。
