---
type: Concept
title: Device 生命周期、资源池与回收线程
description: CANN Runtime Device 的 Init→Start→Stop 生命周期（Device 接口纯虚、RawDevice 实现）、每 Device 持有的 Engine/MemoryPool/EventPool/DeviceSqCqPool/TaskFactory 资源池、与 aclrtSetDevice/aclrtResetDevice 配对的引用计数，以及按 Device 粒度运行的任务回收线程（WakeUpRecycleThread）。
tags:
- task.design
- topic.architecture
- topic.implementation.resource_lifecycle
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/modules/device/device.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/device.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/raw_device.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/runtime.hpp
  role: implementation
created_at: '2026-09-30T00:00:00Z'
updated_at: '2026-11-02T08:02:29Z'
platforms: []
---

# Device 生命周期、资源池与回收线程

本卡蒸馏 Runtime 核心层 Device 的生命周期、资源组成与回收机制，供理解 `aclrtSetDevice`/`aclrtResetDevice` 背后发生了什么、以及 Device 为何能跨 Stream 共享资源时参考。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## 三层继承与接口

Device 对外是抽象接口，经三层继承实现（详见 [Runtime 分层架构](layered_architecture.md)）：[`Device`（接口，`NoCopy`）](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/device.hpp#L161) → `GroupDevice`（设备组）→ [`RawDevice`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/raw_device.hpp#L30)（实际设备）。`Device` 把核心操作声明为纯虚函数，由 `RawDevice` 实现。

## 生命周期：Init → Start → Stop

`aclrtSetDevice` → `Runtime::DeviceRetain(devId, tsId)` 在首次获取该 `[Device][TS]` 槽位时创建 `RawDevice` 并走初始化：

- [`Init()`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/device.hpp#L165)（纯虚）：初始化驱动、获取设备属性、创建资源池。
- [`Start()`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/device.hpp#L168)（纯虚）：启动调度引擎（Engine）、创建主流（PrimaryStream）。
- [`Stop()`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/device.hpp#L171)（纯虚）：在引用计数归零、`DeviceRelease` 时停止调度、释放资源。

引用计数与 [aclrtSetDevice](../apis/device_management/aclrt_set_device.md) 的 Primary Context 引用计数并行维护，均按 `[Device][TS]` 槽位（见 [Context 模型](context_thread_binding_model.md)）；`DeviceRetain`/`DeviceRelease` 按次数配对，计数归零才真正 `Stop()` 并释放。

## 每 Device 持有的资源池

设计文档将 `RawDevice` 持有的核心组件列为：

| 组件 | 职责 |
| --- | --- |
| Engine | 调度引擎，提交/调度任务 |
| MemoryPool / MemoryPoolManager | 设备内存池（见 [Memory 模型](memory_allocation_model.md)） |
| EventPool | Event 对象池（`IsSupportEventPool` 判定） |
| DeviceSqCqPool | SQ/CQ 池，多 Stream 共享复用（见 [Stream SQ/CQ 机制](stream_sqcq_async_mechanism.md)） |
| TaskFactory | Device 粒度任务对象分配（见 [Task 管理](task_management_model.md)） |
| PrimaryStream | Device 主流 |

资源池化是性能设计来源：Event/Memory/SQ-CQ 池复用避免频繁创建销毁，多个 Stream 共享 SQ/CQ。

## 任务回收线程（按 Device 粒度）

任务回收线程挂在 Device 上，而非每个 Stream 一个：

- [`SubmitTask`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/device.hpp#L194) 提交任务；Stream 同步时经 `device_->WakeUpRecycleThread()` 唤醒回收线程异步回收任务资源，不阻塞提交。
- `GetIsDoingRecycling()` 标记回收线程是否在运行，避免重复唤醒。
- 回收线程由 Device 统一驱动，因此一个 Device 上多个 Stream 的任务回收由同一线程异步完成（配合 [Stream 同步机制](stream_sqcq_async_mechanism.md) 的 sqHead 轮询）。

## 状态与异常处理

- [`GetDeviceStatus()`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/device.hpp#L214)（纯虚）返回设备状态，对外经 `rtDeviceStatusQuery` 暴露为 `RT_DEVICE_STATUS_NORMAL`/`RT_DEVICE_STATUS_ABNORMAL`。
- 设计文档的错误处理路径：检测错误 → 设置设备状态 → 停止设备 → 触发回调；设备异常后同步接口返回错误码，上层据此排障。

## 适用条件与失效边界

- 适用：理解 Device 初始化/释放时序、资源池组成与回收线程归属；适用于固定 commit `b523035a` 核心层实现。
- 失效边界：具体资源池集合、Engine/驱动实现随代际（driver v100/v200/v201）与芯片 `config/` 不同；`IsSupportEventPool` 等能力按平台差异；状态枚举与错误处理路径以实际驱动返回为准。
- 验证方式：以 `device/device.hpp`、`device/raw_device.hpp` 与 `runtime.hpp` 的 `DeviceRetain`/`DeviceRelease` 为准；设计文档 `docs/zh/design/modules/device/device.md` 作导读，冲突时以源码为准。

## 相关知识

- [Runtime 分层架构与进程/对象模型](layered_architecture.md)——Device 的三层继承与在对象模型中的位置
- [Context 线程关联与 Primary Context 引用计数模型](context_thread_binding_model.md)——Device 与 Primary Context 的 [Device][TS] 配对
- [Stream SQ/CQ 异步执行与任务回收机制](stream_sqcq_async_mechanism.md)——回收线程与 Stream 同步的配合
- [Device 管理 API](../apis/device_management/index.md)——Device 设置、查询、P2P 与 Reset 接口
