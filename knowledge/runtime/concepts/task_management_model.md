---
type: Concept
title: Task 任务类型、资源管理与下发回收模型
description: CANN Runtime 以 TaskInfo 承载多类任务（计算/内存/事件同步/条件/管理）；任务资源分 Device 粒度（TaskFactory→TaskAllocator 预分配）与 Stream 粒度（TaskResManage）两层；处理函数按驱动版本注册（RegTaskFunc v100/v200/v201）；任务经 Alloc→填 TaskInfo→组 SQE→下发→回收的生命周期。
tags:
- task.design
- topic.architecture
- topic.implementation.resource_lifecycle
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/modules/task/task.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/task/task.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/task/task_res.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/pool/task_allocator.hpp
  role: implementation
created_at: '2026-09-30T04:14:33Z'
updated_at: '2026-11-02T08:02:29Z'
platforms: []
---
# Task 任务类型、资源管理与下发回收模型

本卡蒸馏 Runtime 核心层 Task 的类型体系、资源分层与生命周期，供理解各类 `aclrt*` 下发接口背后的统一任务模型时参考。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## 统一任务载体 TaskInfo 与任务类型

各类操作最终都组装成 `TaskInfo` 并下发。设计文档按 `tsTaskType_t` 将任务分为五类：

| 任务分类   | 代表类型                                                           | 说明                 |
| ---------- | ------------------------------------------------------------------ | -------------------- |
| 计算类     | `TS_TASK_TYPE_KERNEL_AICORE`/`_AICPU`/`_AIVEC`               | 算子核执行           |
| 内存类     | `TS_TASK_TYPE_MEMCPY`                                            | H2D/D2D/D2H 异步拷贝 |
| 事件同步类 | `TS_TASK_TYPE_EVENT_RECORD`/`_STREAM_WAIT_EVENT`/`_NOTIFY_*` | 流间/卡间同步        |
| 条件类     | `TS_TASK_TYPE_LABEL_*`/`_STREAM_SWITCH`/`_STREAM_ACTIVE`     | 标签控制与分支       |
| 管理类     | `TS_TASK_TYPE_MAINTENANCE`/`_MODEL_EXECUTE` 等                 | 资源维护与模型执行   |

## 任务资源的两层管理

任务对象分 Device 与 Stream 两个粒度管理：

- **Device 粒度**：[`TaskFactory`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/task/task.hpp#L232)（`NoCopy`）持有 [`TaskAllocator`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/pool/task_allocator.hpp)（`NoCopy`），**预分配**任务对象以减少分配开销（随 Device 创建）。
- **Stream 粒度**：[`TaskResManage`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/task/task_res.hpp#L30) 管理单条 Stream 的任务资源（`Stream::taskResMang_`），David 平台用派生类 `TaskResManageDavid`。

## 处理函数按驱动版本注册

不同任务类型的初始化、SQE 封装、回收后处理、异常后处理由统一注册的处理函数承担。注册在 `Runtime::Init()` 的 `RegTaskFunc()` 中按驱动版本分派（设计文档）：

- v100：`TaskFuncReg()`
- v200：`RegDavidTaskFunc()` + `RegXpuTaskFunc()`
- v201：`RegDavidTaskFunc()` + 更新 DQS 钩子

这使得新增任务类型或适配新代际芯片可通过注册扩展，而不改动下发主流程。

## 任务生命周期

与 [Stream SQ/CQ 机制](stream_sqcq_async_mechanism.md) 一致，单个任务经历：

1. **分配**：`Stream::AllocTask` → `TaskFactory`/`TaskAllocator` 取出预分配 `TaskInfo`。
2. **填充**：填 `TaskInfo` 字段（类型、Stream、内核/拷贝参数等）。
3. **组 SQE**：按任务类型封装 SQE。
4. **下发**：写入 SQ、经 DRV 层提交到硬件。
5. **回收**：由 Device 粒度的回收线程从完成状态回收任务资源、更新资源池（见 [Device 回收线程](device_lifecycle_and_resources.md)）。

## 适用条件与失效边界

- 适用：理解各类下发接口共用的 TaskInfo 模型、资源两层分配与按版本注册的处理函数；适用于固定 commit `b523035a` 核心层实现。
- 失效边界：任务类型枚举、处理函数注册路径随驱动版本（v100/v200/v201）与平台（David/Xpu/DQS）不同；具体 SQE 字段与下发路径按平台实现。任务类型清单以 `tsTaskType_t` 头文件为准。
- 验证方式：以 `task/task.hpp`（TaskFactory）、`task/task_res.hpp`（TaskResManage）、`pool/task_allocator.hpp` 为准；设计文档 `docs/zh/design/modules/task/task.md` 作导读，冲突时以源码为准。

## 相关知识

- [Stream SQ/CQ 异步执行与任务回收机制](stream_sqcq_async_mechanism.md)——任务组 SQE、下发与同步
- [Device 生命周期、资源池与回收线程](device_lifecycle_and_resources.md)——TaskFactory 归属与回收线程
- [Kernel 二进制加载与执行模型](kernel_program_loading_model.md)——计算类任务执行的内核来源
