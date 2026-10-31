---
type: API
title: aclrtNonBlockingLaunchEnd
description: "结束 NonBlockingLaunchBegin 区间；所有嵌套结束且 Stream 为同步模式时，等待已下发任务完成。"
tags:
- task.lookup
- topic.implementation.synchronization
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/06_stream_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/stream.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_stream.cc
  role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtNonBlockingLaunchEnd

## 功能说明

与 [aclrtNonBlockingLaunchBegin](aclrt_non_blocking_launch_begin.md) 配合使用，标记指定 Stream 上任务异步执行的结束点。所有嵌套的 Begin 调用结束后，若 Stream 为同步模式，本接口会等待已下发任务执行完成。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtNonBlockingLaunchEnd(stream, flag)` 到 RTS 层。

## 函数原型

```c
aclError aclrtNonBlockingLaunchEnd(aclrtStream stream, uint64_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。传入 NULL 表示当前 Context 的默认 Stream。 |
| flag | 输入 | 预留参数，固定配置为 0。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 950、A3、A2 支持。
- 若未先调用 Begin 直接调用 End 返回失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/4_launch_blocking/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/4_launch_blocking/main.cpp#L355)
