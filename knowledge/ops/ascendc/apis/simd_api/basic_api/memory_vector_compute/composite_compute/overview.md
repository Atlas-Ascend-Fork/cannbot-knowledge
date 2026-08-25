---
type: API
title: 复合计算概述
description: 复合计算通常指的是在数学或编程中对复合函数或运算的处理。
tags: [task.lookup, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 复合计算概述

复合矢量计算接口将多个基础运算融合为单条指令，减少中间数据读写和指令开销。
支持的融合模式包括 Axpy、MulAddDst、MulCast、MulsCast、AddRelu、AddReluCast、SubRelu、SubReluCast、AbsSub、ExpSub、FusedMulAdd、MulAddRelu、CastDequant、AddDeqRelu 等。
推荐使用场景：UB 资源紧张时减少 UB 占用；高性能场景减少指令数量；高精度场景在目的操作数精度高于源操作数时获得精度提升。
MulCast、AddReluCast、SubReluCast、MulsCast 包含类型转换操作；CastDequant、AddDeqRelu 涉及量化参数，需结合 SetDeqScale 接口使用。
MulAddDst、FusedMulAdd、MulAddRelu 涉及三操作数读取，若三操作数均不重叠则理论并行度减半，可通过重叠操作数恢复。
