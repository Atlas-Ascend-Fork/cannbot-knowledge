---
type: API
title: aclrtSetOpExecuteTimeOutV2
description: 设置算子执行的超时时间，单位为微秒。返回实际生效的超时时间。
tags:
- task.lookup
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

# aclrtSetOpExecuteTimeOutV2

## 功能说明

设置算子执行的超时时间，单位为微秒。返回实际生效的超时时间。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 委托 `rtSetOpExecuteTimeOutV2(timeout, actualTimeout)` 到 RTS 层。
## 函数原型

```c
aclError aclrtSetOpExecuteTimeOutV2(uint64_t timeout, uint64_t *actualTimeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| timeout | 输入 | 超时时间（微秒）。0表示使用最大超时时间。若最短时间间隔<100000微秒，0表示永不超时。 |
| actualTimeout | 输出 | 返回实际生效的超时时间（微秒）。永不超时时输出 uint64_t 最大值。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明
