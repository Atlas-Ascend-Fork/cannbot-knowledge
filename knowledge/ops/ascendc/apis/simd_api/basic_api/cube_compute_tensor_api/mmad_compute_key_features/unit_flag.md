---
type: API
title: UnitFlag
description: unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C
  Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/mmad_compute_key_features/UnitFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---


# UnitFlag

UnitFlag是Mmad计算的配置参数，用于控制矩阵计算的数据排布和对齐方式。包含isKFull（K轴是否满载）、isNFull（N轴是否满载）等标志，影响Mmad的内部切分和计算策略。

通过MmadTiling中的UnitFlag字段配置。正确配置UnitFlag可以避免不必要的padding计算，提升性能。
