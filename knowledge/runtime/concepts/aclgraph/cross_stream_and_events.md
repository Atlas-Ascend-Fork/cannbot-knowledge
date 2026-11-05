---
type: Concept
title: ACL Graph 跨流捕获与 Event/Notify 同步
description: ACL Graph 跨流捕获通过 Event 在 Stream 间建立依赖，把多个 Stream 的任务捕获到同一模型；捕获期 Event 的 Record/Wait 由 event_capture 处理并记入 CaptureModel.captureEvents_；执行时经 Notify 在执行流与 AddStream 间做执行前/后同步。
tags:
- task.design
- topic.graph_execution
- topic.implementation.synchronization
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/features/aclgraph.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/event_capture.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/model/capture_model.hpp
  role: implementation
created_at: '2026-10-17T03:45:23Z'
updated_at: '2026-11-02T08:20:00Z'
platforms: []
---
# ACL Graph 跨流捕获与 Event/Notify 同步

本卡蒸馏 ACL Graph 跨流捕获的依赖建立与两类同步（捕获期 Event、执行期 Notify）。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## 跨流捕获：用 Event 建立 Stream 间依赖

单流捕获只记录一条流；跨流捕获把多个 Stream 的任务捕获到**同一** CaptureModel。机制是通过 **Event** 建立流间依赖（设计文档）：

1. 主流 `aclmdlRICaptureBegin` 进入捕获；
2. 其他 Stream 通过 `aclrtRecordEvent`/`aclrtStreamWaitEvent` 直接或间接依赖主流，从而一并进入捕获状态；
3. 最终需经 Event 返回主流，实现跨 Stream 任务协同；
4. 另可用 `rtStreamAddToModel` 主动把某 Stream 添加到捕获模型。

因此 Event 既是运行期跨流同步原语（见 [Event 同步机制](../event_synchronization_model.md)），也是捕获期把多流"织"进同一图的依赖载体。

## 捕获期 Event 处理

捕获激活时，Event 的 Record/Wait 不走普通下发，而由 `feature/aclgraph/event_capture.cc` 的捕获分支处理：

- Wait 侧：[`Event::CaptureWaitProcess`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/event_capture.cc#L99)、外部事件 [`ExternalEventWaitProcess`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/event_capture.cc#L109)。
- Record 侧：软件事件 [`RecordSoftwareEvent`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/event_capture.cc#L60) 等。
- 被捕获的 Event 记入模型的 `captureEvents_`（`InsertCaptureEvent`/`GetCaptureEvent`）；EndCapture 时 `ResetCaptureEvents` 复位，避免捕获用事件影响后续执行。

## 执行期 Notify 同步

多流图执行时，执行流与"被添加流"（AddStream）之间用 **Notify** 保证顺序（设计文档 + `capture_model.cc`）：

- **执行前**：[`CaptureModel::SetNotifyBeforeExecute`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L245)——`NotifyRecord(addStream)` → `NotifyWait(exeStream)`，等 AddStream 完成当前任务后再执行图。
- **执行后**：`SetNotifyAfterExecute`——`NotifyRecord(exeStream)` → `NotifyWait(addStream)`，图执行完通知 AddStream 继续。

模型维护 `addStreamNotifyList_`/`executeNotifyList_` 两组 Notify 分别对应添加流同步与执行同步。

## 适用条件与失效边界

- 适用：理解多流捕获如何经 Event 织入同一图、捕获期 Event 的特殊处理与执行期 Notify 的前后同步；适用于固定 commit `b523035a`。
- 失效边界：Event/Notify 的下发随平台（Stars/David、v100/v200）不同（`event_capture_arch5162.cc` 等）；外部事件（`ACL_EVENT_EXTERNAL`）走单独路径。
- 验证方式：以 `feature/aclgraph/event_capture.cc` 与 `feature/aclgraph/capture_model.cc`（SetNotifyBefore/AfterExecute）、`capture_model.hpp`（captureEvents_）为准。

## 相关知识

- [ACL Graph 捕获-执行分离模型与整体架构](overview.md)——AddStream 与多流图总览
- [Event 跨流与跨进程同步机制](../event_synchronization_model.md)——Event 作为运行期同步原语
- [单流捕获与级联流机制](stream_capture_mechanism.md)——单流到多流的扩展
