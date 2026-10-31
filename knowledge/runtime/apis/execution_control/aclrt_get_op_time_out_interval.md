---
type: API
title: aclrtGetOpTimeOutInterval
description: 获取硬件支持的算子超时配置的最短时间间隔，单位为微秒。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.synchronization
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/12_execution_control.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/event.cpp
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

# aclrtGetOpTimeOutInterval

## 功能说明

获取硬件支持的算子超时配置的最短时间间隔，单位为微秒。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 委托 `rtGetOpTimeOutInterval(interval)` 到 RTS 层。
## 函数原型

```c
aclError aclrtGetOpTimeOutInterval(uint64_t *interval)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| interval | 输出 | 最短时间间隔（微秒）。用户可配置的超时时间为 interval * N，N 取值范围 [1, 254]。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明
