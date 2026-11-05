---
type: Concept
title: Runtime 分层架构与进程/对象模型
description: CANN Runtime 的 API/Feature/Core/Driver 四层结构、rt*/aclrt*/aclmdlRI* 三类接口前缀，以及 Runtime 单例→Device→Context→Stream 的对象模型；Primary Context 与 Device 均按 [Device][TS] 维护，"每个设备一个 Primary Context"仅为单 TS 简化。
tags:
- task.design
- topic.architecture
- topic.implementation.resource_lifecycle
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/architecture.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/runtime.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/device.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/group_device.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/raw_device.hpp
  role: implementation
created_at: '2026-09-30T00:00:00Z'
updated_at: '2026-11-02T06:33:43Z'
platforms: []
---
# Runtime 分层架构与进程/对象模型

本卡蒸馏 CANN Runtime 的整体分层与对象模型，供理解 API 之间关系、资源归属与排障入口时参考。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围因设计文档未提供产品支持表而保持未知。

## 四层架构

Runtime 以动态库形式部署在用户态进程，作为上层框架/加速库与内核态驱动之间的桥梁。代码按四层组织，目录与职责一一对应：

| 层                   | 职责                                                                 | 源码目录                                         |
| -------------------- | -------------------------------------------------------------------- | ------------------------------------------------ |
| 接口层（API）        | 对外 C/C++ 接口，统一参数校验与错误码转换                            | `src/runtime/api/`                             |
| 特性层（Feature）    | 基于核心层构筑的可插拔特性                                           | `src/runtime/feature/`                         |
| 核心层（Core）       | Device/Context/Stream/Task/Memory/Kernel/Event/Notify 等最小功能集合 | `src/runtime/core/src/`                        |
| 驱动适配层（Driver） | 按代际芯片屏蔽驱动差异，统一经 HAL 调用                              | `src/runtime/driver/`、`src/runtime/config/` |

- 驱动适配层按代际分目录，固定 commit 下为 `driver/v100`、`driver/v200`、`driver/v201`；芯片差异由 `config/<芯片>` 配置。
- 特性层为独立目录，固定 commit 下包含 `aclgraph`、`snapshot`、`model`、`fusion` 等（另有 `ccu`、`cntnotify`、`ffts`、`soma`、`xpu` 等），支持按目录选择性编译与扩展。

## 三类对外接口前缀

设计文档将对外接口分为三类前缀家族，接口层统一处理参数校验与错误码转换：

- `rt*`：底层运行时接口（如 `rtStreamCreate`），多为内部/底层入口。
- `aclrt*`：ACL 运行时功能接口（如 `aclrtCreateStream`、`aclrtLaunchKernel`），是上层框架常用入口。
- `aclmdlRI*`：ACL Graph/Model 特性接口（如 `aclmdlRICaptureBegin`、`aclmdlRIExecuteAsync`）。

## 核心对象模型

核心对象及其持有关系（源码类名）：

- `Runtime`（[`runtime.hpp`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/runtime.hpp#L177)）是进程内单例，经 `Runtime::Instance()` 访问，集中管理 Device、主 Context、Program/Kernel 注册表（`KernelTable`）与 Profiler 启停。
- `Device` → `Context` → `Stream`：Context 关联一个 Device，Stream 由 Context 创建并持有 Device/Context 引用。
- `Program` → `Kernel`：Program 管理内核二进制，按名称表与 tilingKey 表注册/查找 Kernel。
- `Stream` → `TaskInfo` → `Kernel`：任务信息挂在 Stream 上并指向执行的 Kernel。

Device 对外是抽象接口，实现采用三层继承体系：[`Device`（接口）](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/device.hpp#L161) → [`GroupDevice`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/group_device.hpp#L19) → [`RawDevice`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/device/raw_device.hpp#L30)，实现接口与实现解耦。

## Primary Context/Device 按 [Device][TS] 维护

`Runtime` 单例的 Primary Context 与 Device 数组是二维的，按 **Device 与 TS（Task Scheduler）两维** 维护：

```cpp
// src/runtime/core/inc/runtime.hpp:803-804
RefObject<Context*> priCtxs_[RT_MAX_DEV_NUM][RT_MAX_TS_NUM];
RefObject<Device*>  devices_[RT_MAX_DEV_NUM + 1][RT_MAX_TS_NUM]; // Last one is stub device
```

因此：

- Primary Context 与 Device 引用是按 `[Device][TS]` 槽位维护的，`DeviceRetain(devId, tsId)` 与 `PrimaryContextRetain` 均落到具体 TS 槽位。"一个 Device 一个 Primary Context/Device" 是**单 TS 场景的简化说法**；多 TS 平台上一次 `aclrtSetDevice` 会对每个 TS 槽位分别持有引用（与 [aclrtSetDevice](../apis/device_management/aclrt_set_device.md) 的内部行为一致）。
- `devices_` 的第一维多出一个槽位用作 stub device（`// Last one is stub device`），不要把它当作真实可见 Device 计数。

## 进程模型

- 单进程多 Device：一个进程可经 `aclrtSetDevice` 管理/切换多个 Device。
- 单进程多 Context：一个 Context 关联一个 Device，一个进程可创建多个 Context。
- 单进程多 Stream：一个 Context 可创建多个 Stream 实现任务并行。
- 多进程隔离：不同进程的 Runtime 实例与资源状态完全隔离。

## 适用条件与失效边界

- 适用：理解 Runtime API 的资源归属、层间调用路径与排障切入点；对象关系与继承体系适用于固定 commit `b523035a` 的核心层实现。
- 失效边界：目录名、特性清单、驱动版本目录随代码演进可能变化；具体平台是否支持某特性需按该平台的 `config/` 与产品支持资料确认，本卡不声明平台范围。
- 验证方式：以 `src/runtime/core/` 源码为准核对类名、继承关系与 `Runtime` 单例数组维度；设计文档 `docs/zh/design/architecture.md` 作为导读，但与源码冲突时以源码为准。

## 相关知识

- [Stream SQ/CQ 异步执行与任务回收机制](stream_sqcq_async_mechanism.md)——核心层 Stream 如何经 SQ/CQ 与硬件异步交互
- [Context 线程关联与 Primary Context 引用计数模型](context_thread_binding_model.md)——默认/用户 Context 的生命周期与线程绑定
- [Runtime API](../apis/index.md)——各模块对外接口的语义、约束与来源
