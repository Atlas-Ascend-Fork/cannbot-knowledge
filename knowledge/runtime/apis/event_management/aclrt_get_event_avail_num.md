---
type: API
title: aclrtGetEventAvailNum
description: 查询当前 Device 上可用的 Event 数量。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/07_event_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/event.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_event.cc
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

# aclrtGetEventAvailNum

## 功能说明

查询当前 Device 上可用的 Event 数量。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtsEventGetAvailNum(eventCount)`（即 `rtGetAvailEventNum`）到 RTS 层。

## 函数原型

```c
aclError aclrtGetEventAvailNum(uint32_t *eventCount)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| eventCount | 输出 | 可用 Event 数量。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- IPV350 不支持。
