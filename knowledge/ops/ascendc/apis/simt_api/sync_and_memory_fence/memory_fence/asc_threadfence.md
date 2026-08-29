---
type: API
title: AscThreadfence
description: 内存栅栏接口，保证调用前的全局和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/sync_and_memory_fence/memory_fence/asc_threadfence.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_threadfence

全局内存栅栏函数。保证调用线程在 asc_threadfence() 之前的所有全局内存和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序。适用于生产者-消费者同步、原子计数器、指针更新和多线程共享数据等场景。

函数原型：inline void asc_threadfence()

无参数，无返回值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_sync_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。典型用法：生产者写入数据后调用 asc_threadfence() 确保写入顺序可见，再设置标志位；消费者轮询标志位后读取数据。

<!-- cannbot:related:start -->
## 相关

- [AscSyncthreads](../sync_interface/asc_syncthreads.md)（`related`）：“不阻塞线程，仅约束可见性顺序”说明 asc_threadfence 不是执行会合点，“阻塞当前线程块内所有线程，直到所有线程都执行到该同步点位置”则提供块内会合，二者共同决定共享数据发布协议。
- [同步与内存栅栏简介（同步与内存屏障）](../sync_and_memory_fence_intro.md)（`related`）：使用建议：块内阶段同步用 asc_syncthreads；仅需保证内存写入顺序和可见性用 asc_threadfence 或 asc_threadfence_block；内存栅栏不等价于同步屏障，不等待其他线程；asc_syncthreads 不能用于跨 Block 同步；并发写同一地址时同步和栅栏均不能替代原子操作。；全局内存栅栏函数。保证调用线程在 asc_threadfence() 之前的所有全局内存和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序。；总览给出只需可见性时选择 threadfence 的条件，API 卡落实其全局作用域与非阻塞语义。
- [AscThreadfenceBlock](asc_threadfence_block.md)（`same_topic`）：全局内存栅栏函数。保证调用线程在 asc_threadfence() 之前的所有全局内存和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序。；Block 范围内存栅栏函数。保证当前线程在调用 asc_threadfence_block() 之前的所有内存读写操作对同一线程块内其他线程可见，不阻塞线程，仅约束 Block 范围可见性顺序。。两者都是不阻塞线程的可见性顺序栅栏，核心差异仅是全局范围与同一 Block 范围，属于同一 fence 合同的作用域变体。
<!-- cannbot:related:end -->
