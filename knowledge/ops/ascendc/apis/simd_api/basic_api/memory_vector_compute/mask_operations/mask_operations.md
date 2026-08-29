---
type: API
title: 掩码操作
description: Memory矢量计算掩码操作接口索引页，包含SetMaskCount、SetMaskNorm、SetVectorMask与ResetMask。
tags: [task.lookup, topic.implementation.masking]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/mask_operations/mask_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# 掩码操作

Memory 矢量计算的掩码操作接口集合。SetMaskCount/SetMaskNorm 切换 mask 计数模式与正常模式；SetVectorMask 设置矢量计算的 mask 寄存器；ResetMask 重置 mask 为默认值。mask 用于控制矢量计算的有效元素范围，使用 count 模式后必须调用 ResetMask 恢复，否则影响后续计算。
