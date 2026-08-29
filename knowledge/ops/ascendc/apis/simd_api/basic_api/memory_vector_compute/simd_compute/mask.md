---
type: API
title: SIMD计算掩码
description: Mask（掩码）是Ascend C中用于控制数据元素是否参与计算的标识位序列。每一位掩码对应数据中的一个元素的位置，通过有效位和无效位标记，实现对数据操作的精细化开关控制。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/SIMD_compute/mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Mask

SIMD Mask 机制，控制矢量计算中参与运算的元素。支持 Count 模式（按元素计数）和 Norm 模式（按比特位掩码）。通过 SetVectorMask/SetMaskCount/SetMaskNorm 配置。
