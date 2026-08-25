---
type: API
title: 原子操作概述
description: 数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数据搬运开启原子操作。此时，数据搬运完成后，GM中的最终数据由原始GM数据与新搬运数据共同决定。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/atomic_operations_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# 原子操作总览

原子操作提供对Global Memory的原子性读写能力，确保多核并发场景下数据一致性。包含两类：标量原子操作（AtomicAdd/Cas/Exch/Max/Min，直接对GM地址进行原子运算）和DMA随路原子操作（通过SetAtomicAdd等设置DMA搬运时的随路原子操作类型）。

标量原子操作仅Ascend 950PR/950DT支持；DMA随路原子操作支持更多产品型号。原子操作类型包括加、最大值、最小值、比较交换、交换等。

确定性计算注意事项：浮点数原子累加因不满足结合律，指令乱序可能导致非确定性结果。可通过DisableDmaAtomic禁用DMA原子操作或使用SetAtomicType配置原子类型来控制行为。
