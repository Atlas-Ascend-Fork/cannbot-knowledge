---
type: API
title: 比较与选择
description: 矢量比较与选择接口集，包含 Compare、Compares、Select、GatherMask 及 GetCmpMask/SetCmpMask 等。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/compare_and_select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 比较与选择

Memory 矢量比较与选择接口集合。Compare/Compares 执行逐元素比较，结果可存入寄存器或 mask；GetCmpMask/SetCmpMask(ISASI) 用于读写比较 mask 寄存器；Select 按条件从两个 Tensor 中选取元素；GatherMask 按掩码聚合数据。部分接口支持灵活标量位置，适用于条件计算与数据筛选场景。
