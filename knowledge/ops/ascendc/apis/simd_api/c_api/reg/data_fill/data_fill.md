---
type: API
title: 数据填充
description: 寄存器侧数据填充类接口汇总，提供duplicate及其标量、合并、高位合并等多种数据广播填充能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_fill/data_fill.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数据填充

寄存器侧数据填充接口提供数据广播与填充能力。asc_duplicate将数据复制填充到目标寄存器，asc_duplicate_scalar以标量值填充。
_merge变体（asc_duplicate_merge/asc_duplicate_scalar_merge/asc_duplicate_highest_merge）支持与已有数据合并填充；_highest变体（asc_duplicate_highest）填充高位数据。
