---
type: Concept
title: Stream SQ/CQ 异步执行与任务回收机制
description: CANN Runtime Stream 经 SQ/CQ 提交任务，完成等待按平台、发送回收模式与绑定状态分派。Stars 的相应分支轮询 SQ head，关注任务还需等待回收，部分正常 Event 任务也会请求 CQE。
tags:
- task.design
- topic.architecture
- topic.implementation.synchronization
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/modules/stream/stream.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/task/task_info/event/event_task.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/task/task_info/event/event_task_v100.cc
  role: implementation
created_at: '2026-09-30T04:14:33Z'
updated_at: '2026-11-05T07:05:35Z'
platforms: []
---
# Stream SQ/CQ 异步执行与任务回收机制

本卡蒸馏 Runtime 核心层 Stream 的异步执行与同步/回收机制，供理解 `aclrtLaunchKernel` 下发、`aclrtSynchronizeStream` 等待与任务回收关系时参考。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## SQ/CQ 异步模型

Stream 通过 SQ（Submission Queue，提交队列）与 CQ（Completion Queue，完成队列）实现 Host 与硬件的异步任务交互：

- **任务提交**：Host 侧把一条任务组装成 SQE（Submission Queue Entry）写入 SQ 的 `sqTail` 位置，`sqTail` 前移指向下一个可用槽位。
- **硬件执行**：硬件从 `sqHead` 位置读取 SQE，执行任务后前移 `sqHead`。
- **完成判定**按平台与 Stream 配置选择 SQ head 轮询、任务等待或 Event 同步等路径，具体分支见下文。CQE 可用于指定任务的正常完成报告和异常上报，其生成取决于任务类型与 SQE 标志。

`Stream` 继承自 `NoCopy`，其 SQ/CQ 相关字段（[`stream.hpp`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.hpp#L172)）：

```cpp
uint32_t sqId_;            // SQ ID
uint32_t cqId_;            // CQ ID
uint32_t sqTailPos_;       // SQ 尾位置（Host 提交位置）
uint32_t sqHeadPos_;       // SQ 头位置（硬件处理位置）
uint64_t sqAddr_{0ULL};    // SQ 基地址，max size is 2M
uint32_t sqDepth_;         // SQ 深度
Atomic<uint32_t> taskPosHead_;  // only for stars
Atomic<uint32_t> taskPosTail_;  // only for stars
```

> `taskPosHead_`/`taskPosTail_` 的源码注释标注 `only for stars`。使用这些游标解释完成判定时，需要结合下文的 Stars 分支条件。

## 创建流程（Setup）

`aclrtCreateStream` → `rtStreamCreate` → `StreamFactory::CreateStream` → [`Stream::Setup()`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.cc#L627)。`Setup()` 内部依次：

1. 按 `flags_`（如 `RT_STREAM_HUGE`）与 `Device` 属性设置 SQ 深度；
2. 经驱动分配 `streamId_`；
3. 经 `StreamSqCqManage::AllocStreamSqCq` 分配/复用 `sqId_`/`cqId_`；
4. 分配逻辑 CQ（`AllocLogicCq`）并创建任务资源（`CreateStreamTaskRes`/`CreateStreamArgRes`）。

多 Stream 可共享 SQ/CQ 资源（`StreamSqCqManage` 维护 `sqIdRefMap_` 引用计数复用），这是 SQ/CQ 池化的来源。

## 任务提交流程（AllocTask）

[`Stream::AllocTask`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.cc#L4952) 按 Stream 当前模式分派到不同路径，优先级依次为：

1. TaskGroup 更新路径（捕获的任务组标记更新）；
2. AutoSplit 路径；
3. 捕获路径（`GetCaptureStatus() != NONE`，用于 ACL Graph 流捕获）；
4. 普通非捕获路径（`AllocNonCaptureTask`）。

分配 `TaskInfo` 后填充任务字段（如 AICore 任务的 kernel、args、blockDim），再组装 SQE 写入 SQ，经 DRV 层 `halSqTaskSend` 提交到硬件 SQ，并更新 SQ tail 位置。

## 同步/回收机制

`Stream::Synchronize()` 按以下条件选择等待路径。[同步入口](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.cc#L2081-L2118)

| 条件 | 等待路径 |
| ---- | -------- |
| Stars，`IsSeparateSendAndRecycle()` 为真且 `GetBindFlag()` 为假 | 在 `IsSyncFinished()` 为假时调用 `SynchronizeImpl()` |
| Stars，发送回收未分离或存在绑定标志 | `StarsWaitForTask()` |
| 非 Stars，`GetDisableThread()` 为真 | `WaitForTask()` |
| 非 Stars，`GetDisableThread()` 为假 | 通过前置检查后创建 Event，调用 `Record()` 与 `Synchronize()` 等待完成 |

`IsSeparateSendAndRecycle()` 还要求芯片支持回收线程、流未绑定 DVPP 组、未启用 Software SQ，且排除 AICPU/CP_PROCESS_USE 流。[分离条件](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.cc#L4542-L4546)

### SQ head 轮询分支

`SynchronizeImpl()` → `SynchronizeExecutedTask()` 等待目标任务完成，核心循环如下。[轮询实现](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.cc#L1973-L2026)

- 轮询 `Driver_()->GetSqHead(...)` 获取硬件 `sqHead`；
- 当 `sqHead == posTail`（提交位置，`GetTaskPosTail()`）或目标任务已判定执行完成（`IsTaskExcuted`）即返回成功；
- 循环中若设备未在回收，经 `device_->WakeUpRecycleThread()` 唤醒回收线程处理任务资源。
- 带超时控制（`IsProcessTimeout`），超时返回 `RT_ERROR_STREAM_SYNC_TIMEOUT`。

完成判定后，`concernedTaskId == MAX_UINT16_NUM` 分支唤醒回收线程并返回，对应日志 `no concerned cqe`。指定关注任务时，继续经 `WaitConcernedTaskRecycled()` 等待该任务回收。[完成与回收等待](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.cc#L2058-L2078)

### 正常 Event 的 CQE

Stars 的 timeline 或 Stream 同步 Event 在相应条件下设置 `isCqeNeedConcern`。v100 的 Event SQE 构造在 timeline 或该关注标志有效时设置 `wr_cqe = 1`，请求正常完成 CQE。因此分析等待行为时，需要同时核对任务类型、CQE 标志和关注任务回收条件。[Event 初始化](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/task/task_info/event/event_task.cc#L74-L78)、[SQE 构造](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/task/task_info/event/event_task_v100.cc#L37-L52)

## 适用条件与失效边界

- 适用范围为固定 commit `b523035a` 中 Stream 异步提交、完成等待和资源回收的关系，定位时先核对平台、发送回收模式和绑定状态。
- 失效边界包括平台派生 Stream 的同步实现、任务类型与 SQE/CQE 标志。SQ 基地址上限（2M）、SQ 深度随 Device 属性与 `RT_STREAM_HUGE` 等 flag 变化，具体异常报告需结合驱动层核对。
- 验证方式以 `stream.hpp`/`stream.cc` 核对字段与 `Setup`/`AllocTask`/`Synchronize` 分派，以 `event_task.cc`/`event_task_v100.cc` 核对正常 Event 的 CQE 标志。设计文档作导读。

## 相关知识

- [Runtime 分层架构与进程/对象模型](layered_architecture.md)——Stream 在核心层的位置与对象关系
- [Context 线程关联与 Primary Context 引用计数模型](context_thread_binding_model.md)——Stream 由 Context 创建并归属管理
- [Stream 管理 API](../apis/stream_management/index.md)——Stream 创建、同步、属性与异常处理接口
