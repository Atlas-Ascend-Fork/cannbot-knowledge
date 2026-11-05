---
type: Concept
title: Memory 分配策略、拷贝语义与虚拟内存模型
description: CANN Runtime 的大页/小页分配策略与内存池、物理内存和虚拟地址解耦及 IPC 共享。区分 aclrtMemcpyAsync 的锁页 Host 内存异步下发与非锁页 Host 内存同步回退，说明完成确认要求。
tags:
- task.design
- topic.memory
- topic.implementation.memory_management
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/modules/memory/memory.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/pool/memory_pool.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/pool/memory_pool_manager.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-03_memory_copy_and_set.md
  role: constraint
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_error.cc
  role: implementation
created_at: '2026-09-30T04:14:33Z'
updated_at: '2026-11-05T07:05:35Z'
platforms: []
---
# Memory 分配策略、拷贝语义与虚拟内存模型

本卡蒸馏 Runtime 核心层内存管理的关键模型，供选择分配策略、理解同步/异步拷贝差异与虚拟内存接口组合时参考。接口级细节见内存管理 API 卡；本卡聚焦可复用的模型与权衡。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## 分配策略：大页 vs 小页

`aclrtMalloc(devPtr, size, policy)` 的 `policy` 决定页类型与回退（设计文档）：

| 策略                           | 语义                                 |
| ------------------------------ | ------------------------------------ |
| `ACL_MEM_MALLOC_HUGE_FIRST`  | 优先大页（2MB），不足回退小页（4KB） |
| `ACL_MEM_MALLOC_HUGE_ONLY`   | 仅大页，不足报错                     |
| `ACL_MEM_MALLOC_NORMAL_ONLY` | 仅小页                               |
| `ACL_MEM_MALLOC_HUGE1G_ONLY` | 仅 1G 大页                           |
| `*_P2P` 变体                 | 对应策略的 P2P 场景版本              |

权衡：小页（4KB）更省资源；大页（2MB/1G）处理海量数据时性能更好。另有 `ACL_MEM_TYPE_LOW/HIGH_BAND_WIDTH` 等内存类型与只读访问权限策略。

## 内存池

设备内存由内存池管理以复用、减少频繁向驱动申请/释放：[`MemoryPool`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/pool/memory_pool.hpp#L23)（`NoCopy`）与 [`MemoryPoolManager`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/pool/memory_pool_manager.hpp#L31)（`NoCopy`）。内存池随 Device 创建并归属 Device（见 [Device 资源池](device_lifecycle_and_resources.md)）。

## 拷贝语义：同步 vs 异步

|      | 同步 `aclrtMemcpy`       | 异步 `aclrtMemcpyAsync`                      |
| ---- | -------------------------- | ---------------------------------------------- |
| 行为 | 阻塞 Host 线程直到拷贝完成 | 使用锁页 Host 内存时异步下发到指定 Stream。H2D/D2H 识别到非锁页 Host 内存时，先同步 Stream 再同步拷贝 |
| 适用 | 需在接口返回后使用结果 | 满足异步条件且任务依赖允许时，可安排拷贝与计算重叠 |
| 完成确认 | 成功返回后使用结果 | 异步下发后需经 Event/Stream 同步确认完成。同步回退路径在拷贝完成后返回 |

固定版本 API 文档明确区分锁页 Host 内存（如 `aclrtMallocHost` 申请）与非锁页 Host 内存（如 `malloc` 申请）的返回语义。源码中的非锁页回退执行 `StreamSynchronize(stm, -1)` → `MemCopySync()`。该分支依赖 `IsSupportUserMem()` 支持及地址类型判定，目标环境需结合驱动能力核对。[接口语义](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-03_memory_copy_and_set.md#L140)、[同步回退实现](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_error.cc#L2422-L2438)、[地址检查](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_error.cc#L2971-L3030)

异步下发分支把拷贝封装为内存类 Task（`TS_TASK_TYPE_MEMCPY`），经 Stream 下发（见 [Task 模型](task_management_model.md)）。拷贝方向含 `H2H`/`H2D`/`D2H`/`D2D`/`DEFAULT`（自动推断）及 `INNER`/`INTER_DEVICE_TO_DEVICE`（同设备/跨设备）。批量拷贝 `aclrtMemcpyBatch*` 一次提交多块，减少下发开销。

## 虚拟内存解耦

物理内存管理把"物理内存"与"虚拟地址"解耦，用于跨进程共享、大内存池等进阶场景：

1. `aclrtMallocPhysical` 分配物理内存，得 handle；
2. `aclrtReserveMemAddress` 预留虚拟地址空间，得 virPtr；
3. `aclrtMapMem` 将 handle 映射到 virPtr，建立可访问映射；
4. 释放顺序：`aclrtUnmapMem` → `aclrtReleaseMemAddress` → `aclrtFreePhysical`。

## IPC 内存共享

进程 A `aclrtIpcMemGetExportKey` 导出 key，进程 B `aclrtIpcMemImportByKey` 导入共享内存，用完 `aclrtIpcMemClose`；实现跨进程设备内存共享。

## 适用条件与失效边界

- 适用：选择分配策略、判断同步/异步拷贝、组合虚拟内存与 IPC 接口；适用于固定 commit `b523035a`。
- 失效边界：页大小（2MB/1G）、策略可用性、带宽类型与 P2P/跨设备能力依赖具体芯片与驱动；策略/方向枚举值以 acl 头文件为准。内存池内部结构随实现演进可能变化。
- 验证方式以 `pool/memory_pool.hpp`、`pool/memory_pool_manager.hpp` 核对池机制，以 `api_error.cc` 核对非锁页拷贝分支，接口语义核对固定版本 API 文档，策略与拷贝方向核对 acl 头文件。设计文档作导读。

## 相关知识

- [Device 生命周期、资源池与回收线程](device_lifecycle_and_resources.md)——内存池归属 Device
- [Task 任务类型、资源管理与下发回收模型](task_management_model.md)——异步拷贝作为内存类 Task
- [内存管理 API](../apis/memory_management/index.md)——分配释放、拷贝、虚拟内存与内存池接口
