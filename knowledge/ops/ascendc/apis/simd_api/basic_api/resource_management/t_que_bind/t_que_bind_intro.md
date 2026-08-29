---
type: API
title: TQueBind简介
description: TQueBind绑定源逻辑位置和目的逻辑位置，根据源位置和目的位置，来确定内存分配的位置 、插入对应的同步事件，帮助开发者解决内存分配和管理、同步等问题。Tque是TQueBind的简化模式。通常情况下开发者使用TQue进行编程，TQueBind对外提供一些特殊数据通路的内存管理和同步控制，涉及这些通路时可以直接使用TQueBind。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/TQueBind_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# TQueBind简介

TQueBind绑定源逻辑位置和目的逻辑位置，根据源位置和目的位置，来确定内存分配的位置 、插入对应的同步事件，帮助开发者解决内存分配和管理、同步等问题。Tque是TQueBind的简化模式。通常情况下开发者使用TQue进行编程，TQueBind对外提供一些特殊数据通路的内存管理和同步控制，涉及这些通路时可以直接使用TQueBind。

<!-- cannbot:related:start -->
## 相关

- [纯搬运类算子VECIN和VECOUT建议复用](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/vecin_vecout_reuse.md)（`explains`）：“这种场景可以使用Ascend C针对纯搬运类算子提供的TQueBind接口，该接口可以将UB（VECIN）与UB（VECOUT）绑定，省略将数据从UB（VECIN）拷贝到UB（VECOUT）的步骤，从而避免vector的无谓消耗。”给出优化动作；“TQueBind绑定源逻辑位置和目的逻辑位置，根据源位置和目的位置，来确定内存分配的位置 、插入对应的同步事件，帮助开发者解决内存分配和管理、同步等问题。”给出接口的内存与同步合同，二者直接支撑实现和验证。
<!-- cannbot:related:end -->
