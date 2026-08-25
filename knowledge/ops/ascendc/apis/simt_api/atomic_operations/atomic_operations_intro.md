---
type: API
title: 原子操作简介
description: SIMT原子操作用于保证对同一地址的一次读-改-写过程具有原子性，可避免多个线程并发更新同一地址时出现更新丢失。原子操作常用于计数、状态抢占、直方图统计、归约计算和共享状态位更新等场景。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/atomic_operations_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 原子操作简介

SIMT原子操作用于保证对同一地址的一次读-改-写过程具有原子性，可避免多个线程并发更新同一地址时出现更新丢失。原子操作常用于计数、状态抢占、直方图统计、归约计算和共享状态位更新等场景。
SIMT原子操作用于保证对同一地址的一次读-改-写过程具有原子性，可避免多个线程并发更新同一地址时出现更新丢失。原子操作常用于计数、状态抢占、直方图统计、归约计算和共享状态位更新等场景。

原子操作保证单次内存更新不可被其他线程打断，但不保证多个线程到达该原子操作的先后顺序，也不能替代线程同步屏障功能。

<!-- cannbot:related:start -->
## 相关

- [原子操作（AI Core SIMT编程）](../../../guides/programming_guide/programming_model/ai_core_simt_programming/atomic_operations.md)（`explains`）：指南解释 SIMT 线程并发访问 GM/UB 时为何需要原子读改写，并给出数据竞争语境。
- [原子操作边界值汇总（附录）](../../appendix/atomic_operations_interface_boundary_value_summary.md)（`related`）：边界值汇总补充各原子接口在特殊输入下的返回和写回结果，用于构造正确性测试。
- [asc_atomic_and](asc_atomic_and.md)（`same_topic`）：asc_atomic_and 与《原子操作简介》的实质衔接是：atomic AND 与其他 SIMT 原子读改写及 atomic store 配置共享并发更新契约。
- [asc_atomic_exch](asc_atomic_exch.md)（`same_topic`）：asc_atomic_exch 与《原子操作简介》的实质衔接是：SIMT、C scalar 与基础 API 的 AtomicExch 都实现同址原子交换；SIMT 原子简介补充返回旧值和并发顺序约束。
- [asc_atomic_xor](asc_atomic_xor.md)（`same_topic`）：asc_atomic_xor 与《原子操作简介》的实质衔接是：SIMT atomic xor 与 C scalar 对应入口操作同一原子异或，SIMT 原子简介补充旧值返回和并发顺序。
- [原子操作](atomic_operations.md)（`same_topic`）：原子操作 与《原子操作简介》的实质衔接是：SIMT 原子操作卡定义 GM/UB 作用域、读改写原子性以及不提供执行顺序；SIMT 指南、边界值表和 SIMD 原子概述用于选择作用域并验证边界，而不是替代同步。
<!-- cannbot:related:end -->
