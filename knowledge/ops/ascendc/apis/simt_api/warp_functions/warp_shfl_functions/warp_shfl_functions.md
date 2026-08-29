---
type: API
title: Warp Shfl类函数
description: 提供Warp级别的数据交换接口。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_shfl_functions/Warp_shfl_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Warp Shfl类函数

提供 Warp 内的数据交换接口，包括同步交换（asc_shfl）、前缀交换（asc_shfl_up）、后缀交换（asc_shfl_down）和蝶形交换（asc_shfl_xor）。这些函数允许同一 Warp 内不同 Lane 之间直接交换寄存器数据，无需经过共享内存，适用于 Warp 级别的并行规约和数据重排。
