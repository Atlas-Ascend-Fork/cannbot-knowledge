---
type: API
title: aclrtGetNotifyId
description: 获取指定 Notify 的 ID。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/08_notify_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/notify.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtGetNotifyId

## 功能说明

获取指定 Notify 的 ID。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtGetNotifyIdImpl`（notify.cpp:70）对 notify 与 notifyId 均做空校验，通过 `rtsNotifyGetId(static_cast<rtNotify_t>(notify), notifyId)` 读取。

## 函数原型

```c
aclError aclrtGetNotifyId(aclrtNotify notify, uint32_t *notifyId);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| notify | 输入 | 指定要查询的 Notify。 |
| notifyId | 输出 | Notify ID。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | notify 或 notifyId 为空指针 | 提供有效参数 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | RTS 层查询失败 | 检查 Notify 状态 |