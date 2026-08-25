---
type: API
title: AscCopyGm2UbAlign
description: 提供数据非对齐搬运功能，将数据从GM搬运到UB，支持8位/16位/32位数据类型，包含不同架构版本实现。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_gm2ub_align/asc_copy_gm2ub_align.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# AscCopyGm2UbAlign

Global Memory到Unified Buffer对齐数据搬运接口集合，支持按指定对齐要求将数据从GM搬运到UB。相比asc_copy_gm2ub，本接口支持配置L2 Cache管理策略（通过asc_load_l2_cache_mode枚举指定），可优化重复数据访问场景的搬运效率。按硬件架构版本区分：asc_copy_gm2ub_align_arch_2201适用于Atlas A2/A3系列，asc_copy_gm2ub_align_arch_3510适用于Ascend 950PR/950DT。
