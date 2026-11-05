---
type: Concept
title: ACL Graph TaskGroup 任务组与模型更新
description: ACL Graph 通过 TaskGroup 标记与更新已捕获任务，或用分界点拆分模型。模型级参数修改先进入 UPDATING，再经 aclmdlRIUpdate 更新为 READY 或 FAULT，CanUpdate 同时检查模型运行状态。
tags:
- task.design
- topic.graph_execution
- topic.implementation.resource_lifecycle
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/features/aclgraph.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/context_aclgraph.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/model/capture_model.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model_utils.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_impl_standard_soc.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_impl.cc
  role: implementation
created_at: '2026-10-17T03:45:23Z'
updated_at: '2026-11-05T07:05:35Z'
platforms: []
---
# ACL Graph TaskGroup 任务组与模型更新

本卡蒸馏 ACL Graph 捕获后的任务/模型更新机制，供理解动态 Shape 或参数调整场景下如何复用图时参考。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## 两种更新方式

设计文档给出两种任务更新路径：

- **分界点捕获**：把待更新任务前后拆成多段模型分别执行，适合**大量**任务更新。
- **任务组标记更新**：用 `aclmdlRICaptureTaskGrpBegin/End` 标记一个待更新的任务组，支持并发更新，适合**少量**任务更新。

## TaskGroup 结构

[`TaskGroup`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.hpp#L138)（`stream.hpp`）记录一组任务的位置与更新标记：

```cpp
struct TaskGroup {
    std::vector<std::pair<uint16_t, uint16_t>> taskIds; // streamId + taskId
    bool isUpdate{false};
    uint32_t updateTaskIndex{0};
};
```

- 开始：[`Context::StreamBeginTaskGrp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/context_aclgraph.cc#L122) 检查任务组状态（`StreamTaskGroupStatus`，重复开始或正在更新则报 `RT_ERROR_STREAM_TASKGRP_STATUS`），新建 `TaskGroup` 并绑定到捕获流的当前任务组。
- 结束：`StreamEndTaskGrp` 返回 handle；若模型已失效或任务组出错则返回空 handle，否则经 `AddTaskGroupList` 挂到模型 `taskGroupList_`。
- 更新：`aclmdlRICaptureTaskUpdateBegin(stream, handle)` → 执行新任务 → `aclmdlRICaptureTaskUpdateEnd`，更新路径经 Stream 的 TaskGroup 更新分支（`IsTaskGroupUpdate()`，见 [Stream AllocTask 分派](../stream_sqcq_async_mechanism.md)）。

## 模型级参数更新

任务组更新使用 `StreamTaskGroupStatus` 与 TaskGroup 的更新标记。模型级参数修改使用 `RtCaptureModelStatus`，两套状态分别维护。

1. 参数修改前，内部 `CheckCaptureModelForUpdate()` 检查 Software SQ 支持、顶层捕获模型与运行状态。`CanUpdate()` 要求模型未运行，且状态为 `READY` 或 `UPDATING`。[更新前检查](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model_utils.cc#L244-L272)、[状态条件](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/model/capture_model.hpp#L131-L136)
2. `TaskSetParams()` 等修改操作在通过前置检查后将模型置为 `UPDATING`，再修改任务参数。参数修改阶段失败时将模型置为 `FAULT`。[参数修改实现](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_impl_standard_soc.cc#L1561-L1599)
3. 调用 `aclmdlRIUpdate(captureModel)` 后，`ApiImpl::ModelUpdate()` 先检查 Software SQ 能力，再按模型状态处理。在 `READY` 状态直接成功返回，在 `UPDATING` 状态调用 `CaptureModel::Update()`，成功转为 `READY`，失败转为 `FAULT`。其他状态返回更新失败。[模型更新实现](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_impl.cc#L7492-L7517)

## 适用条件与失效边界

- 适用：在动态 Shape/参数调整下复用捕获图、选择分界点 vs 任务组更新；适用于固定 commit `b523035a`。
- 失效边界：`StreamBeginTaskGrp` 位于 `Context`（`context_aclgraph.cc:122`），而捕获的 Begin/End 入口位于 `CaptureSession`；更新能力与并发度随平台实现不同。
- 验证方式以 `stream.hpp`（TaskGroup 结构）、`context_aclgraph.cc`（任务组更新）、`capture_model.hpp`（CanUpdate）、`api_impl_standard_soc.cc`（参数修改）和 `api_impl.cc`（ModelUpdate）为准。

## 相关知识

- [ACL Graph 捕获-执行分离模型与整体架构](overview.md)——捕获入口与对象总览
- [捕获模式与状态机](capture_modes_and_status.md)——模型运行状态及 READY、UPDATING、FAULT 的判定
- [Stream SQ/CQ 异步执行与任务回收机制](../stream_sqcq_async_mechanism.md)——AllocTask 的 TaskGroup 更新分支
