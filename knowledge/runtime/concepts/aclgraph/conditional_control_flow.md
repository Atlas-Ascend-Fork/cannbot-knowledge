---
type: Concept
title: ACL Graph 条件控制流（IF/WHILE/SWITCH）与子模型
description: ACL Graph 经 CondHandle（NoCopy，持 device 条件值内存与子模型列表）实现 IF/WHILE/SWITCH 动态分支；父 CaptureModel 管理若干 CondHandle，每个 CondHandle 的多个子模型共用一个 Notify，资源随父模型申请释放；条件任务用 2 个（IF/SWITCH）或 3 个（WHILE，含 JumpBack）SQE。
tags:
- task.design
- topic.graph_execution
- topic.implementation.resource_lifecycle
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/features/aclgraph.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/cond_handle/cond_handle.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/context_aclgraph.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
created_at: '2026-10-17T03:45:23Z'
updated_at: '2026-11-02T08:20:00Z'
platforms: []
---
# ACL Graph 条件控制流（IF/WHILE/SWITCH）与子模型

本卡蒸馏 ACL Graph 条件控制流的对象模型与资源管理，供理解在捕获图中实现动态分支/循环时参考。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## 条件类型与整体流程

条件控制流让捕获图在执行时按**条件值**选择子图分支（[`acl_rt.h`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h#L1075) 定义）：

| 类型                              | 值 | size（分支数） |
| --------------------------------- | -- | -------------- |
| `ACL_MODEL_RI_COND_TYPE_IF`     | 0  | 1 或 2         |
| `ACL_MODEL_RI_COND_TYPE_WHILE`  | 1  | 1              |
| `ACL_MODEL_RI_COND_TYPE_SWITCH` | 2  | >0             |

流程：父模型捕获中 → `aclmdlRICondHandleCreate` 创建条件句柄 → `aclmdlRICondHandleGetCondPtr` 拿到条件值 device 指针（用户自定义算子可改写）→ `aclmdlRIAddCondTask` 下发条件任务并创建子模型 → 各子模型经 `aclmdlRICaptureToModelRIBegin`/`aclmdlRICaptureEnd` 分别捕获 → 父模型 EndCapture（要求所有子模型已结束）→ 执行时条件值决定走哪个子模型。

## CondHandle：条件值与子模型容器

[`CondHandle`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/cond_handle/cond_handle.hpp#L24)（`: public NoCopy`）归属一个父 CaptureModel，持有条件值 device 内存与子模型列表：

- `devAddr_`：存储条件值的 device 指针（`Setup` 时 `DevMemAlloc` 分配并初始化为 0）。
- `subCaptureModels_`：该句柄的子模型列表。
- `subModelNotify_`：**同一 CondHandle 下所有子模型共用一个 Notify**，避免重复申请。
- `flag_`：`ACL_MODEL_RI_COND_HANDLE_ASSIGN_DEFAULT` 时，模型执行前把条件值初始化为 `defaultValue_`。

父模型侧维护 `condHandles_`（句柄列表）与 `condHandleTaskMap_`（`StoreCondHandleTaskInfo` 记录 streamId+taskId→CondHandle）。子模型由 [`Context::CreateSubCaptureModels`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/feature/aclgraph/context_aclgraph.cc#L251) 按 `params.size` 创建，`SetSubCaptureModel()` 标记、`SetCondHandle` 绑定。

## 关键设计决策

1. **子模型共用 Notify**：同一 CondHandle 下子模型共享一个 Notify，id 在执行时统一申请刷新。
2. **资源随父模型管理**：子模型的 SQ/CQ、Notify 由父模型 `BuildSqCq` 阶段统一 `AllocAllSqCq`/`ReleaseAllSqCq`，子模型不单独释放。
3. **EndCapture 同步检查**：`CheckSubModelsIsEndCapture` 确认所有子模型 READY，否则返回 `ACL_ERROR_RT_SUB_ACLGRAPH_IS_CAPTURING`。
4. **条件值初始化**：执行前 `InitAllSubCaptureModelCondTaskByDefValue`（当 flag 为 ASSIGN_DEFAULT）。
5. **条件任务 SQE 刷新**：执行时 `UpdateCondTaskFuncCallMemAll` 重构 FunctionCall 内存。
6. **可嵌套**：子模型内部可再建 CondHandle，支持多级条件嵌套。

## 条件任务 SQE 结构

| SQE    | 名称                               | 适用            |
| ------ | ---------------------------------- | --------------- |
| SQE[0] | CondFirst（条件判断 FunctionCall） | IF/WHILE/SWITCH |
| SQE[1] | NotifyWait（等子模型完成通知）     | IF/WHILE/SWITCH |
| SQE[2] | JumpBack（跳回循环头）             | 仅 WHILE        |

对应常量：`COND_TASK_IF_SWITCH_SQE_NUM = 2`、`COND_TASK_WHILE_SQE_NUM = 3`（`core/src/task/inc/aclgraph_cond_task.h`）。

## 适用条件与失效边界

- 适用：在捕获图中实现 IF/WHILE/SWITCH 动态控制流、理解子模型资源归属；适用于固定 commit `b523035a`。
- 失效边界：CondOp 需设备支持；条件类型 size 约束与 SQE 结构随实现/平台不同。条件类型枚举值以 acl 头文件为准。
- 验证方式：以 `cond_handle/cond_handle.hpp`（CondHandle）、`feature/aclgraph/context_aclgraph.cc`（CreateSubCaptureModels）、`core/src/task/inc/aclgraph_cond_task.h`（SQE 常量）与 `acl_rt.h`（条件类型）为准。

## 相关知识

- [ACL Graph 捕获-执行分离模型与整体架构](overview.md)——父子模型与对象总览
- [捕获模式与状态机](capture_modes_and_status.md)——子模型 READY 检查
- [跨流捕获与 Event/Notify 同步](cross_stream_and_events.md)——Notify 在子模型中的复用
