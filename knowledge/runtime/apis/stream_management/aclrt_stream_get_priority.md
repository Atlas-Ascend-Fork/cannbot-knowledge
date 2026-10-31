---
type: API
title: aclrtStreamGetPriority
description: 查询指定 Stream 的优先级。
tags:
- task.lookup
- topic.implementation.resource_query
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
updated_at: '2026-10-29T08:46:01Z'
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

# aclrtStreamGetPriority

## 功能说明

查询指定 Stream 的优先级。传入 NULL 获取默认 Stream 的优先级。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtStreamGetPriority(stream, &prio)` 到 RTS 层。

## 函数原型

```c
aclError aclrtStreamGetPriority(aclrtStream stream, uint32_t *priority)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。传入 NULL 获取默认 Stream 优先级。 |
| priority | 输出 | 优先级，数字越小优先级越高。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/3_stream_config_query/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/3_stream_config_query/main.cpp#L78)
