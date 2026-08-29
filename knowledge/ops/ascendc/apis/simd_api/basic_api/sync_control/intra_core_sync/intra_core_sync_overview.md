---
type: API
title: 核内同步能力概述
description: AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并行的方式运行，在读写同一存储资源时可能存在数据依赖关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/intra_core_sync_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 核内同步能力概述

AI Core 内部的执行单元（如 MTE2 搬运单元、Vector 计算单元等）以异步并行方式运行，在读写同一存储资源时可能存在数据依赖关系，需通过同步控制协调操作时序确保数据一致性。
硬件流水类型包括 PIPE_S（标量）、PIPE_V（矢量）、PIPE_M（矩阵）、PIPE_MTE1、PIPE_MTE2、PIPE_MTE3、PIPE_FIX 等。
核内同步分为两类：多流水同步用于不同类型流水间的依赖控制，通过 SetFlag/WaitFlag 或 Lock/Unlock 接口实现；单流水同步用于相同类型流水间的顺序控制，通过 PipeBarrier 接口实现。
Ascend 950PR/950DT 新增 Lock/Unlock 接口，相比 SetFlag/WaitFlag 内聚性更强且支持更多同步信号量。
TPipe-TQue 框架和毕昇编译器支持自动同步，部分场景仍需开发者手动插入同步。
