---
type: API
title: AscThreadfenceBlock
description: Block范围内存栅栏接口，保证调用前的内存读写操作对同一线程块内其他线程可见，不阻塞线程，仅约束Block范围可见性。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/sync_and_memory_fence/memory_fence/asc_threadfence_block.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_threadfence_block

Block 范围内存栅栏函数。保证当前线程在调用 asc_threadfence_block() 之前的所有内存读写操作对同一线程块内其他线程可见，不阻塞线程，仅约束 Block 范围可见性顺序。相比 asc_threadfence 仅需保证 Block 内共享缓存层级一致性，无需全局内存屏障。

函数原型：inline void asc_threadfence_block()

无参数，无返回值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_sync_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [同步机制（AI Core SIMT编程）](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/synchronization.md)（`explains`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；AscThreadfenceBlock正文说明“Block范围内存栅栏接口，保证调用前的内存读写操作对同一线程块内其他线程可见，不阻塞线程，仅约束Block范围可见性”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [AscSyncthreads](../sync_interface/asc_syncthreads.md)（`related`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《AscThreadfenceBlock》明确“Block范围内存栅栏接口，保证调用前的内存读写操作对同一线程块内其他线程可见，不阻塞线程，仅约束Block范围可见性。”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [ThreadBlockTile协作组sync](../../cooperative_groups/thread_block_tile/sync.md)（`related`）：ThreadBlockTile协作组sync 与《AscThreadfenceBlock》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [同步与内存栅栏](../sync_and_memory_fence.md)（`related`）：asc_threadfence_block 把可见性限制在同一 Block，适用于无需全局屏障的低范围生产者—消费者关系。
- [同步与内存栅栏简介（同步与内存屏障）](../sync_and_memory_fence_intro.md)（`related`）：简介把 threadfence_block 定位为不阻塞线程的块内内存顺序与可见性约束，可用于只需发布数据、不需所有线程会合的场景。
- [AscThreadfence](asc_threadfence.md)（`same_topic`）：AscThreadfence 提供设备范围内的内存可见性，block 变体只保证线程块范围；二者的选择由消费者作用域决定。
- [内存栅栏接口](memory_fence.md)（`same_topic`）：《内存栅栏接口》处理“提供线程与块级别的内存栅栏接口。”。《AscThreadfenceBlock》提供“Block范围内存栅栏接口，保证调用前的内存读写操作对同一线程块内其他线程可见，不阻塞线程，仅约束Block范围可见性。”，其具体合同或探针直接接入SIMT fence 的可见性范围、线程同步差异和具体 block/global 接口。
<!-- cannbot:related:end -->
