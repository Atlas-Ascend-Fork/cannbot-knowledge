---
type: API
title: aclrtNonBlockingLaunchBegin
description: "开始 Stream 的异步下发区间，使同步流或 LAUNCH_BLOCKING 模式下的 Launch 保持异步；须与 End 配对，可嵌套。"
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

# aclrtNonBlockingLaunchBegin

## 功能说明

与 [aclrtNonBlockingLaunchEnd](aclrt_non_blocking_launch_end.md) 配合使用，标记指定 Stream 上任务异步执行的起始点。当 ASCEND_RT_LAUNCH_BLOCKING=1 或 Stream 为同步模式时，Begin/End 区间内的 Launch 接口保持异步。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtNonBlockingLaunchBegin(stream, flag)` 到 RTS 层。flag 为预留参数，固定传 0。

## 函数原型

```c
aclError aclrtNonBlockingLaunchBegin(aclrtStream stream, uint64_t flag)
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
- 不支持 ACL_STREAM_PERSISTENT、ACL_STREAM_CPU_SCHEDULE、ACL_STREAM_DEVICE_USE_ONLY 类型的 Stream。
- 需与 NonBlockingLaunchEnd 成对使用，支持嵌套调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/4_launch_blocking/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/4_launch_blocking/main.cpp#L349)
