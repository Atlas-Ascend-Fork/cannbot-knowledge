---
type: API
title: 原子操作
description: SIMT API原子操作类接口汇总，提供add、sub、exch、max、min、inc、dec、cas等原子运算能力。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/atomic_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 原子操作

SIMT原子操作保证对同一地址的单次读-改-写过程具有原子性，避免多线程并发更新丢失。提供asc_atomic_add/sub/exch/max/min/inc/dec/cas/and/or/xor，适用于计数、状态抢占、直方图统计、归约等场景。
原子操作可作用于Global Memory（Grid内可访问）和Unified Buffer（线程块内可访问）。GM原子操作以128B地址范围为粒度，目标地址分散可提升吞吐；UB原子操作延迟较低但作用范围限于当前线程块。
原子操作保证单次更新不被打断，但不保证线程执行顺序，也不能替代同步屏障。浮点累加要求逐bit一致时应使用固定顺序归约。

<!-- cannbot:related:start -->
## 相关

- [原子操作（AI Core SIMT编程）](../../../guides/programming_guide/programming_model/ai_core_simt_programming/atomic_operations.md)（`explains`）：原子操作 与《原子操作（AI Core SIMT编程）》的实质衔接是：SIMT 原子操作卡定义 GM/UB 作用域、读改写原子性以及不提供执行顺序；SIMT 指南、边界值表和 SIMD 原子概述用于选择作用域并验证边界，而不是替代同步。
- [原子操作概述](../../simd_api/basic_api/atomic_operations/atomic_operations_overview.md)（`related`）：原子操作 与《原子操作概述》的实质衔接是：SIMT 原子操作卡定义 GM/UB 作用域、读改写原子性以及不提供执行顺序；SIMT 指南、边界值表和 SIMD 原子概述用于选择作用域并验证边界，而不是替代同步。
- [原子操作概述（SIMD原子操作）](../../simd_api/c_api/simd_atomic/atomic_operations_overview.md)（`related`）：原子操作 与《原子操作概述（SIMD原子操作）》的实质衔接是：SIMT 原子操作卡定义 GM/UB 作用域、读改写原子性以及不提供执行顺序；SIMT 指南、边界值表和 SIMD 原子概述用于选择作用域并验证边界，而不是替代同步。
- [原子操作边界值汇总（附录）](../../appendix/atomic_operations_interface_boundary_value_summary.md)（`related`）：原子操作 与《原子操作边界值汇总（附录）》的实质衔接是：SIMT 原子操作卡定义 GM/UB 作用域、读改写原子性以及不提供执行顺序；SIMT 指南、边界值表和 SIMD 原子概述用于选择作用域并验证边界，而不是替代同步。
- [原子操作简介](atomic_operations_intro.md)（`same_topic`）：原子操作 与《原子操作简介》的实质衔接是：SIMT 原子操作卡定义 GM/UB 作用域、读改写原子性以及不提供执行顺序；SIMT 指南、边界值表和 SIMD 原子概述用于选择作用域并验证边界，而不是替代同步。
<!-- cannbot:related:end -->
