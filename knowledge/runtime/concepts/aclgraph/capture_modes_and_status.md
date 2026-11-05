---
type: Concept
title: ACL Graph 捕获模式与状态机
description: ACL Graph 的 GLOBAL/THREAD_LOCAL/RELAXED 模式控制不安全操作的限制范围与结束捕获的线程约束。区分 Stream 捕获状态和 CaptureModel 生命周期，说明 READY、UPDATING 与模型运行状态对更新的影响。
tags:
- task.design
- topic.graph_execution
- topic.implementation.resource_lifecycle
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/features/aclgraph.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/model/capture_model.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_session.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model_utils.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/common/inner_thread_local.cpp
  role: implementation
created_at: '2026-10-17T03:45:23Z'
updated_at: '2026-11-05T07:05:35Z'
platforms: []
---
# ACL Graph 捕获模式与状态机

本卡蒸馏 ACL Graph 的捕获模式与两级状态机，供理解多线程捕获行为与模型可执行/可更新判定时参考。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## 捕获模式与不安全操作限制

`aclmdlRICaptureBegin(stream, mode)` 传入捕获模式（[`acl_rt.h`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h#L412) 定义）：

下表按调用线程的 exchange mode 为默认值 `GLOBAL` 说明各模式引入的限制。默认值见固定实现。[线程局部初始值](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/common/inner_thread_local.cpp#L22-L23)

| 模式 | 值 | 不安全操作的限制范围 |
| ---- | -- | -------------------- |
| `ACL_MODEL_RI_CAPTURE_MODE_GLOBAL` | 0 | 当前 Context 存在 GLOBAL 捕获时，相关线程调用受捕获模式检查的接口会被限制 |
| `ACL_MODEL_RI_CAPTURE_MODE_THREAD_LOCAL` | 1 | 限制当前捕获线程调用受捕获模式检查的接口 |
| `ACL_MODEL_RI_CAPTURE_MODE_RELAXED` | 2 | 本次捕获放宽上述检查，实际许可还受其他捕获与线程 exchange mode 影响 |

`IsCaptureModeSupport()` 综合 Context 捕获模式、线程捕获模式和线程 exchange mode 决定是否允许操作。`aclmdlRICaptureThreadExchangeMode` 可调整调用线程的 exchange mode。[模式检查实现](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_session.cc#L40-L68)

结束捕获时另行检查线程。GLOBAL、THREAD_LOCAL 要求 `aclmdlRICaptureEnd` 与 Begin 在同一线程调用。RELAXED 允许跨线程结束。[线程检查实现](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model_utils.cc#L76-L87)

Context 级捕获模式按**最小值**聚合（`CaptureModeEnter` 中 `mode < GetContextCaptureMode()` 时收紧），并用 `captureModeRefNum_[mode]` 引用计数；退出时递减并据此回退 Context 模式。模式按线程进入/退出（`ThreadCaptureModeEnter/Exit`）。

## 两级状态机

### Stream 级：rtStreamCaptureStatus

单条 Stream 的捕获状态 [`captureStatus_`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/stream/stream.hpp#L728)：

- `RT_STREAM_CAPTURE_STATUS_NONE`：未捕获（可 BeginCapture）。
- `RT_STREAM_CAPTURE_STATUS_ACTIVE`：正在捕获。
- `RT_STREAM_CAPTURE_STATUS_INVALIDATED`：捕获已失效。

### CaptureModel 级：RtCaptureModelStatus

图模型的生命周期状态 [`RtCaptureModelStatus`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/model/capture_model.hpp#L35)（6 态，源码注释）：

| 状态                    | 含义                   |
| ----------------------- | ---------------------- |
| `NONE`                | 初始                   |
| `CAPTURE_ACTIVE`      | 正在捕获               |
| `CAPTURE_INVALIDATED` | 捕获失效               |
| `UPDATING`            | 正在更新               |
| `FAULT`               | 故障                   |
| `READY`               | 捕获或更新完成，可执行 |

捕获阶段经 BeginCapture 进入 `CAPTURE_ACTIVE`，成功 EndCapture 后进入 `READY`。`TerminateCapture` 将 `CAPTURE_ACTIVE` 标记为 `CAPTURE_INVALIDATED`。`IsCaptureReady()` 以 `READY` 为判定条件。[捕获状态转换](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_model.cc#L908-L916)

模型级参数修改使模型进入 `UPDATING`，随后 `aclmdlRIUpdate` 执行更新，成功转为 `READY`，失败转为 `FAULT`，具体调用顺序见 [模型级参数更新](task_group_and_update.md#模型级参数更新)。`CanUpdate()` 要求模型未运行，且状态为 `READY` 或 `UPDATING`。[状态判定实现](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/model/capture_model.hpp#L107-L136)

> 注意：`aclmdlRICaptureStatus`（ACL 层，NONE/ACTIVE/INVALIDATED 三态）面向 Stream 捕获状态查询，与 `RtCaptureModelStatus`（runtime 层，6 态模型生命周期）是不同枚举，不要混用。

## 子模型状态约束

条件控制流的子模型（见 [条件控制流](conditional_control_flow.md)）由 `SetSubCaptureModel()` 标记；父模型 EndCapture 时 `CheckSubModelsIsEndCapture` 检查所有子模型是否已完成 EndCapture（均 READY），否则返回 `ACL_ERROR_RT_SUB_ACLGRAPH_IS_CAPTURING`。

## 适用条件与失效边界

- 适用：选择捕获模式、理解模型可执行/可更新判定与失效路径；适用于固定 commit `b523035a`。
- 失效边界：模式聚合与线程引用计数行为随实现演进；ACL 层与 runtime 层状态枚举需区分使用。模式数值以 acl 头文件为准。
- 验证方式以 `capture_session.cc`（模式检查）、`capture_model_utils.cc`（结束捕获的线程检查）、`capture_model.hpp`（状态判定）、`stream.hpp`（captureStatus）与 `acl_rt.h`（捕获模式）为准，设计文档作导读。

## 相关知识

- [ACL Graph 捕获-执行分离模型与整体架构](overview.md)——三阶段分离与对象总览
- [单流捕获与级联流机制](stream_capture_mechanism.md)——Stream 捕获状态的使用
- [TaskGroup 任务组与模型更新](task_group_and_update.md)——UPDATING 状态的来源
