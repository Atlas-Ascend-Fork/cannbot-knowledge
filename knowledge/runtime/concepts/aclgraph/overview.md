---
type: Concept
title: ACL Graph 捕获-执行分离模型与整体架构
description: ACL Graph（流捕获）将 Stream 任务序列捕获为可复用 CaptureModel，捕获-构建-执行三阶段分离，把任务下沉 Device 减少 Host 下发开销；核心对象 CaptureSession/CaptureModel/Stream captureStatus/级联流/TaskGroup/Notify。
tags:
- task.design
- topic.architecture
- topic.graph_execution
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/features/aclgraph.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_session.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_session.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/model/capture_model.hpp
  role: implementation
created_at: '2026-10-17T03:45:23Z'
updated_at: '2026-11-02T08:20:00Z'
platforms: []
---
# ACL Graph 捕获-执行分离模型与整体架构

本卡蒸馏 ACL Graph（流捕获）特性的核心模型与架构，作为 aclgraph 子主题的总览入口。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## 为什么需要 ACL Graph

在 Eager（边下发边执行）模式下，每个任务都由 Host 单独下发，Host 下发开销随性能优化深入逐渐成为瓶颈。ACL Graph 把一段 Stream 任务序列**捕获**为可复用的图（`CaptureModel`），之后多次**执行**时将任务下沉到 Device，减少 Host 侧重复下发开销。

## 捕获-构建-执行三阶段分离

| 阶段 | 入口                                               | 行为                                                       |
| ---- | -------------------------------------------------- | ---------------------------------------------------------- |
| 捕获 | `aclmdlRICaptureBegin` → `aclmdlRICaptureEnd` | 任务被记录到 CaptureStream 而**非立即执行**          |
| 构建 | `aclmdlRICaptureEnd`                             | 结束捕获，构建可执行图结构                                 |
| 执行 | `aclmdlRIExecuteAsync`                           | `BuildSqCq` 动态绑定 SQ/CQ，提交优化后的任务，可多次执行 |

捕获期间禁止对 Stream、Event、Device、Context 做同步或查询操作（设计文档约束）。

## 核心对象

- **CaptureSession**（[`capture_session.hpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_session.hpp#L27)，`final : public ContextExtension`）：捕获流程控制入口，持有 [`StreamBeginCapture`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_session.cc#L269)/`StreamEndCapture`、捕获模式管理等。
- **CaptureModel**（[`capture_model.hpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/model/capture_model.hpp#L82)，`: public Model`）：捕获的图结构，管理 SQ/CQ 动态绑定、Notify 同步、Event 捕获、TaskGroup、CondHandle 子模型。
- **Stream**：维护捕获状态 `captureStatus_` 与捕获流 `captureStream_`（见 [单流捕获机制](stream_capture_mechanism.md)）。
- **级联流（CaptureStream）**：捕获流 SQ 深度不足时自动创建，续接任务序列。
- **TaskGroup / Notify / Event**：任务组更新、执行前后同步、跨流依赖。

## 设计文档偏差：捕获入口是 CaptureSession 而非 Context

设计文档（`docs/zh/design/features/aclgraph.md`）把捕获流程写成 `Context::StreamBeginCapture`/`StreamEndCapture`（并给出 `context_aclgraph.cc` 的行号）。固定 commit `b523035a` 源码中，这些入口实现在 [`CaptureSession`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/capture_session.cc#L269)（一个 `ContextExtension`），不在 `Context`。此外设计文档正文多处代码的文件行号与当前源码不一致（已漂移）。**定位实现以 `feature/aclgraph/` 源码为准，设计文档仅作导读。**

## 子主题导航

- [单流捕获与级联流机制](stream_capture_mechanism.md)
- [捕获模式与状态机](capture_modes_and_status.md)
- [跨流捕获与 Event/Notify 同步](cross_stream_and_events.md)
- [TaskGroup 任务组与模型更新](task_group_and_update.md)
- [条件控制流（IF/WHILE/SWITCH）与子模型](conditional_control_flow.md)

## 适用条件与失效边界

- 适用：理解 ACL Graph 的价值、三阶段分离与对象关系；适用于固定 commit `b523035a`。
- 失效边界：芯片按 `feature/aclgraph/v100`、`v200` 适配，Software SQ 等能力依赖设备特性（`RT_FEATURE_MODEL_ACL_GRAPH_SOFTWARE_ENABLE` 等）；接口与类结构随版本演进。
- 验证方式：以 `feature/aclgraph/`（CaptureSession/stream_capture/capture_model）与 `core/inc/model/capture_model.hpp` 为准；设计文档作导读，冲突时以源码为准。

## 相关知识

- [Stream SQ/CQ 异步执行与任务回收机制](../stream_sqcq_async_mechanism.md)——捕获替代的是普通 Eager 下发路径
- [模型运行实例管理 API](../../apis/model_running_instance_management/index.md)——aclmdlRI* 捕获/执行接口
