---
type: API
title: 总体约束说明（概述）
description: 所有数据搬运接口共享若干通用约束规则，在进行任何搬运操作前都应确保这些约束被满足，否则可能导致未定义行为或数据异常。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/overview/overall_constraints.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 总体约束说明（概述）

地址对齐要求：GM 1B、UB/L1 32B、L0A/L0B 512B、L0C 64B、BiasTable 64B、Fixpipe 128B。DataBlock（32B）为搬运基本寻址粒度。具体接口有不同对齐要求时以接口说明为准；不满足对齐时使用 DataCopyPad。

多指令同步：多个 DataCopy 目的地址重叠时需调用 PipeBarrier 插入同步（MTE3 流水用 PipeBarrier<PIPE_MTE3>()，MTE2 流水用 PipeBarrier<PIPE_MTE2>()），保证串行化。
