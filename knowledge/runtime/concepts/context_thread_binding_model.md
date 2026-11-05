---
type: Concept
title: Context 线程关联与 Primary Context 引用计数模型
description: CANN Runtime 的默认 Context（aclrtSetDevice，primaryCtx=true）与用户 Context（aclrtCreateContext，primaryCtx=false）两类形态、经 TLS（curCtx_/curRef_）的线程关联、Primary Context 按 [Device][TS] 的引用计数复用，以及 6 态生命周期状态机与 USER/INTERNAL 访问模式。
tags:
- task.design
- topic.architecture
- topic.implementation.resource_lifecycle
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/modules/context/context.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/context/context.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/context/context_manage.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/context/context.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/common/inner_thread_local.hpp
  role: implementation
created_at: '2026-09-30T00:00:00Z'
updated_at: '2026-11-02T06:33:43Z'
platforms: []
---
# Context 线程关联与 Primary Context 引用计数模型

本卡蒸馏 Runtime 核心层 Context 的两类形态、线程关联与生命周期模型，供理解无显式 Context 参数的 Runtime API 如何定位执行环境、以及默认/用户 Context 的创建销毁差异时参考。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## 两类 Context 形态

Context 关联一个 Device，管理默认 Stream、用户 Stream、Model、Module 及错误状态。构造函数是同一个，由 `primaryCtx` 布尔区分形态（[`context.cc`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/context/context.cc#L228)、[`context.hpp`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/context/context.hpp#L108)）：

| 形态         | 创建入口                 | 构造                    | 生命周期管理                                                                                                                                                           |
| ------------ | ------------------------ | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 默认 Context | `aclrtSetDevice()`     | `Context(dev, true)`  | 由 Device 设置/复位路径管理，`Runtime` 用 `RefObject<Context*>` 维护对象及**引用计数**；`aclrtResetDevice` 释放关联资源但**保留 Context 对象供复用** |
| 用户 Context | `aclrtCreateContext()` | `Context(dev, false)` | 由 `ContextManage` 登记，`aclrtDestroyContext()` 显式销毁；对象最终删除受线程绑定引用计数控制                                                                      |

- 默认 Context 不能用 `aclrtDestroyContext` 销毁；用户 Context 不能通过 Reset 释放。
- `ContextState::CTX_STATE_NOT_INITIALIZED` 源码注释为 "Not set up, or reset and waiting for reuse"，印证 reset 后对象保留待复用。

## Primary Context 引用计数按 [Device][TS] 维护

`Runtime` 单例以二维数组按 **Device 与 TS 两维**维护 Primary Context 引用：

```cpp
// src/runtime/core/inc/runtime.hpp:803
RefObject<Context*> priCtxs_[RT_MAX_DEV_NUM][RT_MAX_TS_NUM];
```

- `aclrtSetDevice` → `Runtime::PrimaryContextRetain` 对目标槽位引用计数加一；首次从 0 恢复时创建（或复用已保存的）Context 并 `AttachDevice`，非 0 时直接复用 ACTIVE Context。
- 引用计数进程级，与 `aclrtResetDevice` 按次数配对；多 TS 平台上一次 Set 会对该 Device 的每个 TS 槽位分别持有引用。"一个 Device 一个 Primary Context" 是**单 TS 简化说法**（与 [Runtime 分层架构](layered_architecture.md) 及 [aclrtSetDevice](../apis/device_management/aclrt_set_device.md) 一致）。

## 线程关联（TLS）

无显式 Context 参数的 Runtime API 通过**线程局部存储**定位当前 Context，实现线程间隔离。`InnerThreadLocalContainer`（[`inner_thread_local.hpp`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/common/inner_thread_local.hpp#L20)）维护两个线程局部槽位：

```cpp
static __THREAD_LOCAL__ Context* curCtx_;                 // 显式绑定的 Context（aclrtSetCurrentContext/CreateContext）
static __THREAD_LOCAL__ RefObject<Context*>* curRef_;     // SetDevice 建立的 Primary Context 引用
```

- `aclrtSetCurrentContext`/`aclrtCreateContext` 写入 `curCtx_`（显式绑定）。
- `aclrtSetDevice` 写入 `curRef_` 并**清空** `curCtx_`，因此 SetDevice 会覆盖此前的显式绑定；解析当前 Context 时综合两个槽位（`GetBoundContext`）。
- 线程绑定不跨线程继承：每个使用 Runtime API 的线程需各自 `aclrtSetDevice` 或 `aclrtSetCurrentContext`；用户 Context 可被多线程复用（各线程 `aclrtSetCurrentContext` 指向同一 Context）。

## 生命周期状态机与访问模式

Context 以状态机保障有效性与并发销毁安全。`ContextState`（[`context.hpp`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/context/context.hpp#L77)）共 6 态：

| 状态                          | 含义                           |
| ----------------------------- | ------------------------------ |
| `CTX_STATE_NOT_INITIALIZED` | 未建立，或已 reset 等待复用    |
| `CTX_STATE_INITIALIZING`    | Setup 进行中，仅内部路径可访问 |
| `CTX_STATE_ACTIVE`          | 就绪，可被用户 API 访问        |
| `CTX_STATE_FINALIZING`      | 销毁进行中，用户 API 访问被拒  |
| `CTX_STATE_FINALIZED`       | 销毁完成，资源尚未完全释放     |
| `CTX_STATE_DEINITIALIZING`  | 正在释放资源或删除 Context     |

访问模式 `ContextAccessMode`（[`context_manage.hpp`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/context/context_manage.hpp#L20)）区分 `USER=0` 与 `INTERNAL=1`：`INITIALIZING`/`FINALIZING` 等过渡态仅允许内部路径访问，用户 API（USER）在非 ACTIVE 态被拦截，从而隔离建立/拆除期的并发访问。

## 适用条件与失效边界

- 适用：理解默认/用户 Context 的创建销毁差异、线程如何定位 Context、以及 SetDevice 为何覆盖显式绑定；适用于固定 commit `b523035a` 核心层实现。
- 失效边界：多 TS 平台的 Primary Context 按 TS 槽位独立，单 TS 推论不可直接外推；状态机与访问模式的具体拦截点随实现演进可能变化。
- 验证方式：以 `context.hpp`/`context_manage.hpp`/`context.cc` 与 `inner_thread_local.hpp` 为准核对构造参数、状态枚举、访问模式与 TLS 槽位；设计文档 `docs/zh/design/modules/context/context.md` 作导读，冲突时以源码为准。

## 知识

- [Runtime 分层架构与进程/对象模型](layered_architecture.md)——Context 在对象模型中的位置与 [Device][TS] 维护
- [Stream SQ/CQ 异步执行与任务回收机制](stream_sqcq_async_mechanism.md)——Stream 由 Context 创建并归属管理
- [Context 管理 API](../apis/context_management/index.md)——Context 创建、销毁、切换与系统参数接口
- [aclrtSetDevice](../apis/device_management/aclrt_set_device.md)——建立默认 Context 与线程绑定的入口
