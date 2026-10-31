---
type: API
title: aclrtGetOpExecuteTimeout
description: "查询算子实际执行超时，返回毫秒值；已设置时返回实际值，未设置时返回默认超时。"
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
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/device.cpp
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

# aclrtGetOpExecuteTimeout

## 功能说明

获取算子执行的超时时间。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 委托 `rtGetOpExecuteTimeoutV2(timeoutMs)` 到 RTS 层。
## 函数原型

```c
aclError aclrtGetOpExecuteTimeout(uint32_t *const timeoutMs)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| timeoutMs | 输出 | 超时时间（毫秒）。若已通过set接口设置，返回实际超时时间；否则返回默认超时时间。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明
