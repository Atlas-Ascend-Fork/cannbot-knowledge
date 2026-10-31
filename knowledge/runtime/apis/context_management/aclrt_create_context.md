---
type: API
title: aclrtCreateContext
description: "显式创建并绑定当前线程的 Context，自带默认 Stream；同一 Device 可有多个 Context，独立于 SetDevice 的默认 Context 引用计数。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/05_context_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/context.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_context.cc
  role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtCreateContext

## 功能说明

在当前线程中显式创建 Context，并将当前线程与新创建的 Context 相关联。若不显式创建，系统使用调用 [aclrtSetDevice](../device_management/aclrt_set_device.md) 时隐式创建的默认 Context。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtCtxCreateEx(context, RT_CTX_NORMAL_MODE, deviceId)` 到 RTS 层，RTS 分配 Context 资源并包含一个默认 Stream。
- 创建成功后调用 `UpdatePlatformInfoWithDevice(deviceId)` 更新平台信息；该步骤失败仅记 WARN 日志，不影响返回值。
- 不修改 [aclrtSetDevice](../device_management/aclrt_set_device.md) 的 Primary Context 引用计数；显式 Context 的 TLS 槽位独立于默认 Context 绑定。

## 函数原型

```c
aclError aclrtCreateContext(aclrtContext *context, int32_t deviceId)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| context | 输出 | Context 的指针。 |
| deviceId | 输入 | 指定 Device ID，取值范围 [0, 可用 Device 数)。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。内部通过 rtCtxCreateEx 返回值经 ACL_GET_ERRCODE_RTS 映射后输出。

## 约束说明

- 同一 Device 上可创建多个 Context，Stream 数量受硬件上限制约。
- 未调用 [aclrtSetDevice](../device_management/aclrt_set_device.md) 时首次调用本接口，系统内部会为该 Device 绑定一个默认 Stream。
- 本接口创建的 Context 可被同一进程的多线程共用，但同一时刻一个线程只能使用其中一个 Context。
- IPV350 不支持默认 Context 和默认 Stream。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/context/0_context_query/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/context/0_context_query/main.cpp#L57)
- [`1_basic_features/event/0_event_status/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/0_event_status/main.cpp#L34)
- [`1_basic_features/event/1_event_timestamp/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/1_event_timestamp/main.cpp#L39)
