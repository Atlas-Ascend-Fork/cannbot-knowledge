---
type: API
title: aclrtSetCurrentContext
description: "切换当前线程使用的 Context，跨 Device 时随之切换 Device；多次设置以最后一次为准。"
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

# aclrtSetCurrentContext

## 功能说明

设置当前线程的 Context。若新 Context 与当前 Context 所属 Device 不同，Device 也随之切换。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtCtxSetCurrent(context)` 到 RTS 层，更新 TLS 中的当前 Context 槽位。
- 本接口会覆盖 [aclrtSetDevice](../device_management/aclrt_set_device.md) 建立的默认 Context 绑定；[aclrtSetDevice](../device_management/aclrt_set_device.md) 也会清空本接口建立的显式绑定。

## 函数原型

```c
aclError aclrtSetCurrentContext(aclrtContext context)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| context | 输入 | 指定为当前线程的 Context。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 若给线程设置的 Context 对应的 Device 已被复位，则设置失败。
- 多次调用以最后一次为准。
- 推荐在创建 Context 的线程中使用；跨线程使用时需自行保证 Stream 任务顺序。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/context/0_context_query/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/context/0_context_query/main.cpp#L59)
- [`2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp#L67)
- [`2_advanced_features/kernel/4_launch_blocking/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/4_launch_blocking/main.cpp#L157)
