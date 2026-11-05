---
type: Concept
title: Event 跨流与跨进程同步机制
description: CANN Runtime Event（继承 NoCopy）在 Stream 记录位置、其他 Stream 经 StreamWaitEvent 等待实现跨流同步；支持 Host 阻塞 Synchronize、状态查询、计时（ElapsedTime）与 IPC 跨进程同步；Event Flag（SYNC/TIME_LINE/IPC 等）决定创建分支与同步行为。
tags:
- task.design
- topic.architecture
- topic.implementation.synchronization
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/modules/event/event.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/event/event.hpp
  role: implementation
created_at: '2026-09-30T00:00:00Z'
updated_at: '2026-11-02T08:02:29Z'
platforms: []
---

# Event 跨流与跨进程同步机制

本卡蒸馏 Runtime 核心层 Event 的同步语义与形态，供理解跨 Stream 依赖、Host 等待、计时与 IPC 同步时参考。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## 核心同步模型

`Event`（[`event.hpp`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/event/event.hpp#L59)，继承 `NoCopy`）用于**流间任务同步**：在一个 Stream 的任务序列中记录一个"位置"，另一个 Stream 等待该位置到达，从而建立跨 Stream 依赖。四个核心方法：

- [`Record(stm)`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/event/event.hpp#L71)：在 `stm` 当前位置记录事件（`aclrtRecordEvent`）。
- [`Wait(stm, timeout)`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/event/event.hpp#L72)：让 `stm` 等待事件完成（`aclrtStreamWaitEvent`），实现跨流同步。
- [`Query()`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/event/event.hpp#L74)：查询事件记录状态（`aclrtQueryEventStatus`），非阻塞。
- [`Synchronize(timeout)`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/event/event.hpp#L77)：**Host 侧阻塞**等待事件完成（`aclrtSynchronizeEvent`），确保该事件之前的 Stream 任务全部执行完毕。

与 [Stream 同步](stream_sqcq_async_mechanism.md)（等待整条流完成）不同，Event 允许**部分同步**（只等到记录点）与**跨流/跨进程**依赖。

## Event Flag 决定形态与行为

Event 经 `aclrtCreateEventWithFlag`/`aclrtCreateEventExWithFlag` 传入 Flag，不同 Flag 走不同创建分支与同步行为（设计文档值）：

| Flag | 值 | 用途 |
| --- | --- | --- |
| `ACL_EVENT_SYNC` | 0x01 | 同步事件（Host 阻塞等待计算结果） |
| `ACL_EVENT_CAPTURE_STREAM_PROGRESS` | 0x02 | 流捕获进度标记（ACL Graph） |
| `ACL_EVENT_TIME_LINE` | 0x08 | 时间线事件，用于计时 |
| `ACL_EVENT_DEVICE_USE_ONLY` | 0x10 | 仅设备内部使用 |
| `ACL_EVENT_EXTERNAL` | 0x20 | aclgraph external 标注 |
| `ACL_EVENT_IPC` | 0x40 | IPC 进程间同步 |

处理路径分流：普通 DavidEvent 的 Record/Wait 经 `EvtRecord`/`EvtWait` 入口；IpcEvent 经 `IpcEventRecordStarsV2`/`IpcEventWaitStarsV2` 入口。

## 典型用法

- **跨流同步**：`aclrtRecordEvent(event, stream1)` + `aclrtStreamWaitEvent(stream2, event)`——stream2 等待 stream1 的记录点。
- **计时**：两个 `ACL_EVENT_TIME_LINE` 事件分别 Record 起止点，`Synchronize` 后 `aclrtEventElapsedTime` 得到毫秒间隔。计时前必须同步等待两个 Event 完成。
- **IPC 跨进程**：进程 A `ACL_EVENT_IPC` 创建并 Record，`aclrtIpcGetEventHandle` 导出 handle；进程 B `aclrtIpcOpenEventHandle` 打开后 `aclrtStreamWaitEvent` 等待，经共享内存实现跨进程同步。

## 状态枚举

- `aclrtEventRecordedStatus`：`NOT_READY(0)` / `COMPLETE(1)`（记录是否完成）。
- `aclrtEventWaitStatus`：`COMPLETE(0)` / `NOT_READY(1)` / `RESERVED(0xFFFF)`（等待状态）。

## 适用条件与失效边界

- 适用：理解 Event 的记录/等待/查询/阻塞四种语义、Flag 对形态的影响，以及跨流/计时/IPC 三类场景；适用于固定 commit `b523035a` 核心层实现。
- 失效边界：Flag 的数值与可用组合、DavidEvent/IpcEvent 的下发路径随平台（Stars/David）与版本不同；计时精度与 IPC 能力依赖硬件与驱动支持。Flag 数值为设计文档结论，接入具体版本时以 acl 头文件为准。
- 验证方式：以 `event/event.hpp` 的类与方法为准；Flag/状态枚举核对 acl 头文件；设计文档 `docs/zh/design/modules/event/event.md` 作导读，冲突时以源码为准。

## 相关知识

- [Stream SQ/CQ 异步执行与任务回收机制](stream_sqcq_async_mechanism.md)——Event 记录/等待在 Stream 任务序列中的位置
- [Runtime 分层架构与进程/对象模型](layered_architecture.md)——Event 与 Device/Context 的关联
- [Event 管理 API](../apis/event_management/index.md)——Event 创建、记录、查询、同步与跨进程接口
