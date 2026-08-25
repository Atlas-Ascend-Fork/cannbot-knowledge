---
type: API
title: 比较与选择
description: 寄存器侧比较与选择类接口汇总，提供eq、ge、gt、le、lt、ne等逐元素比较及select、squeeze选择能力。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/compare_and_select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 比较与选择

寄存器侧比较与选择接口提供逐元素比较和条件选择能力。比较运算含asc_eq/ge/gt/le/lt/ne及对应_scalar标量变体，生成掩码结果。
asc_select根据掩码进行条件选择，asc_squeeze对紧凑数据进行解压提取。asc_squeeze_with_status和asc_squeeze_v2已废弃，建议使用asc_squeeze。
