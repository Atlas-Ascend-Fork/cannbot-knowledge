---
type: API
title: UnitFlag
description: unitFlag的核心功能体现为：Mmad和FixPipe接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C
  Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_key_features/UnitFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# UnitFlag

Mmad 和 Fixpipe 接口的单元标志机制，以 L0C Buffer 512B 内存块为粒度实现精细化数据同步，降低同步延迟。unitFlag=2 时开启但不改变标志位（Mmad 写等待 flag=0 后写入保持 0；Fixpipe 读等待 flag=1 后读取保持 1）；unitFlag=3 时开启并改变标志位（Mmad 写后设 1；Fixpipe 读后设 0）。

K 轴迭代场景：前 n-1 次 Mmad 设 unitFlag=2 保持写入能力，最后 1 次设 3 通知 Fixpipe 可读；Fixpipe 设 3 读后恢复为 0。需配合 SetMMColumnMajor/SetMMRowMajor 设置方向：Fixpipe 开启 NZ2ND/ChannelMerge 时用 SetMMRowMajor，否则用 SetMMColumnMajor。Mmad 和 Fixpipe 须同步开启 unitFlag，建议计算量与搬出量一致，否则可通过 SetFixPipeConfig() 重置 L0C Buffer 状态。
