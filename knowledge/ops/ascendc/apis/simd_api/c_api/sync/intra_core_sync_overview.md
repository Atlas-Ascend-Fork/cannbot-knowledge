---
type: API
title: 核内同步能力概述
description: AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并行的方式运行，在读写同一存储资源时可能存在数据依赖关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/intra_core_sync_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 核内同步能力概述

AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并行的方式运行，在读写同一存储资源时可能存在数据依赖关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。硬件流水类型包括PIPE_S（标量）、PIPE_V（矢量计算）、PIPE_M（矩阵计算）、PIPE_MTE1（L1到L0搬运）、PIPE_MTE2（GM到L1/UB搬运）、PIPE_MTE3（UB到GM搬运）、PIPE_FIX（L0C到GM搬运）。

核内同步分为多流水同步和单流水同步：多流水同步通过asc_sync_notify/asc_sync_wait或asc_lock/asc_unlock接口控制不同类型流水间的依赖；单流水同步通过asc_sync_pipe接口保证同一流水内前序指令完成后才执行后续指令。asc_sync_data_barrier接口可阻塞后续指令直到此前内存访问全部完成。
