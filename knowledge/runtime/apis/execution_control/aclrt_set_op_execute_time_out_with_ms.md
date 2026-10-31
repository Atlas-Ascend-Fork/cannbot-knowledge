---
type: API
title: aclrtSetOpExecuteTimeOutWithMs
description: 设置算子执行的超时时间，单位为毫秒。当前未在产品中实际支持。
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
platforms: []

source_headers:
- include/external/acl/acl_rt.h
---

# aclrtSetOpExecuteTimeOutWithMs

## 功能说明

设置算子执行的超时时间，单位为毫秒。当前未在产品中实际支持。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 委托 `rtSetOpExecuteTimeOutWithMs(timeout)` 到 RTS 层。各产品型号均标记为不支持。
## 函数原型

```c
aclError aclrtSetOpExecuteTimeOutWithMs(uint32_t timeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| timeout | 输入 | 超时时间（毫秒）。0表示使用最大超时时间。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明
