---
type: API
title: 比较与选择
description: 寄存器矢量比较与选择接口集合，涵盖Compare、Compares、Select和Squeeze等操作。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/compare_and_select/compare_and_select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 比较与选择

Reg 矢量比较与选择接口集合。Compare/Compares 执行逐元素比较；Select 按条件从两个 Tensor 中选取元素；Squeeze 用于压缩指定维度。相比 Memory 版本接口更精简，结果直接保存在寄存器中，适合需要低延迟比较的场景。
