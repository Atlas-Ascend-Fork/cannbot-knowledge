---
type: API
title: aclrtGetPrimaryCtxState
description: "查询指定 Device 的默认 Context 是否激活；active 返回 0 或 1，预留参数 flags 必须传 NULL。"
tags:
- task.lookup
- topic.implementation.resource_query
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

# aclrtGetPrimaryCtxState

## 功能说明

获取指定 Device 的默认 Context 状态（激活/未激活）。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtsGetPrimaryCtxState(deviceId, &tmp, active)`（即 `Api::Instance()->GetPrimaryCtxState`）到 RTS 层。
- ACL 层校验 flags 必须为 nullptr，否则返回 ACL_ERROR_INVALID_PARAM。

## 函数原型

```c
aclError aclrtGetPrimaryCtxState(int32_t deviceId, uint32_t *flags, int32_t *active)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | 指定 Device ID。 |
| flags | 输入 | 预留参数，当前固定传 NULL。 |
| active | 输出 | 默认 Context 状态：0=未激活，1=激活。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- flags 必须为 NULL，否则报错。
- IPV350 不支持。
