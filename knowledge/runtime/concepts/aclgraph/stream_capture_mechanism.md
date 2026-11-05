---
type: Concept
title: ACL Graph 单流捕获与级联流机制
description: ACL Graph 单流捕获记录任务，SQ 深度不足时通过级联流续接，扩展规模受资源容量约束。Software SQ 在执行前按需绑定 SQ/CQ，后续回放可复用，资源回收、更新或销毁路径按条件释放。
tags:
- task.design
- topic.graph_execution
- topic.implementation.kernel_launch
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/features/aclgraph.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/stream_capture.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/context_aclgraph.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/context_standard_soc_aclgraph.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.hpp
  role: implementation
created_at: '2026-10-17T03:45:23Z'
updated_at: '2026-11-05T08:10:01Z'
platforms: []
---
# ACL Graph 单流捕获与级联流机制

本卡蒸馏 ACL Graph 单流捕获的记录机制、级联流扩展与 Software SQ 动态绑定。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## Stream 的捕获状态

每个 Stream 维护一个捕获状态 [`captureStatus_`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.hpp#L1136)（`rtStreamCaptureStatus`，经 [`GetCaptureStatus()`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.hpp#L728) 读取），取值 `NONE`/`ACTIVE`/`INVALIDATED`；并持有一个捕获流 [`GetCaptureStream()`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.hpp#L745)。`aclmdlRICaptureBegin` 要求状态为 `NONE`，否则返回 `RT_ERROR_STREAM_CAPTURED`（已在捕获中）。

## 捕获期：任务被记录而非下发

捕获激活后，`aclrtLaunchKernel` 等下发在 Stream 内部走捕获分支：`AllocTask` 检测到 `GetCaptureStatus() != NONE` 时转到 [`AllocCaptureTaskImpl`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/stream_capture.cc#L72)（见 [Stream SQ/CQ 机制](../stream_sqcq_async_mechanism.md) 的 AllocTask 分派）：任务被**分配到捕获流并记录任务信息**（累加 `captureSqeNum`），不立即提交硬件。

## 级联流：SQ 深度不足自动扩流

单个捕获流的 SQ 深度有限。当已记录的 `captureSqeNum` + 预留逼近 `GetSqDepth()` 时，自动创建**级联流**续接：

1. [`AllocCascadeCaptureStream`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/stream_capture.cc#L34) 创建新捕获流；
2. `CondStreamActive` 用 Stream Active 任务把新级联流接到当前流之后；
3. `UpdateCascadeCaptureStreamInfo` 更新捕获流信息，后续任务切到新流。

级联流可突破单条流的 SQ 深度限制，扩展规模仍受流、任务内存等资源容量约束。流创建、模型关联或任务分配失败会返回错误，并使捕获失效。[级联流创建与模型关联](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/context_aclgraph.cc#L55)、[级联失败处理](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/stream_capture.cc#L34)、[任务分配失败处理](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/stream_capture.cc#L105)

Software SQ 模式下，`BuildSqCq` 还会统计当前模型及子模型的逻辑 SQ 总数，超过 `RT_DEVICE_SQCQ_RES_MAX_NUM` 时返回 `RT_ERROR_DRV_NO_RESOURCES`。因此，级联扩展还受到执行前 SQ/CQ 构建的容量限制。[逻辑 SQ 统计](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L1163)、[容量检查](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L1198)

## Software SQ 动态绑定（执行阶段）

当设备支持 Software SQ（`RT_FEATURE_MODEL_ACL_GRAPH_SOFTWARE_ENABLE` 等特性同时满足）时，`BeginCapture` 阶段 `SetSoftwareSqEnable()`。执行前，`CaptureModel::BuildSqCq` 根据已有资源决定复用或分配并绑定 SQ/CQ。[BuildSqCq](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L1175)

- 首次执行或资源回收后，`AllocAllSqCq` 经 `AllocSqCqAndBindInternal` 按逻辑 SQ 数量分配 SQ/CQ，并为逻辑 SQ 分配 Device 地址。[资源分配](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L1950)
- `BindSqCq` 更新各流 SQ/CQ 信息，并经 `SqSwitchStreamBatch` **批量切换**流到 SQ。[绑定与切换](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L1321)
- 后续回放遇到已有 `sqCqArray_` 且 `sqCqNum_ != 0` 时，增加 `refCount_` 并复用资源。[重复执行分支](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L1186)
- 正常执行完成时，`CaptureModelExecuteFinish` 递减 `refCount_`，SQ/CQ 可继续保留供后续回放使用。[执行完成处理](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L1542)

资源回收、模型更新或常规销毁路径会调用 `ReleaseSqCqAndNotifyId`。该函数在 `sqCqNum_ > 0` 且 `refCount_ == 0` 时继续释放流程，解绑 SQ/CQ 并经 `FreeSqCqLazy` 归还资源。[资源回收入口](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/context_standard_soc_aclgraph.cc#L15)、[更新入口](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L1563)、[销毁入口](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L111)、[释放条件与流程](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L1268)

## 适用条件与失效边界

- 适用：理解捕获期任务记录、级联流扩展与 Software SQ 执行期绑定；适用于固定 commit `b523035a`。
- 失效边界：Software SQ 依赖设备特性与驱动 `FEATURE_TRSDRV_SQ_SUPPORT_DYNAMIC_BIND`，不支持时走普通模式；级联阈值含预留量随 Device 属性（`expandStreamRsvTaskNum`）不同。
- 资源不足可能使级联捕获失效，或导致执行前 SQ/CQ 构建失败。
- 验证方式：以 `feature/aclgraph/stream_capture.cc`（AllocCaptureTaskImpl/AllocCascadeCaptureStream）、`feature/aclgraph/capture_model.cc`（BuildSqCq/BindSqCq）与 `stream.hpp` 的 captureStatus 为准。

## 相关知识

- [ACL Graph 捕获-执行分离模型与整体架构](overview.md)——三阶段分离与对象总览
- [Stream SQ/CQ 异步执行与任务回收机制](../stream_sqcq_async_mechanism.md)——AllocTask 的捕获/非捕获分派
- [捕获模式与状态机](capture_modes_and_status.md)——captureStatus 的取值与转换
