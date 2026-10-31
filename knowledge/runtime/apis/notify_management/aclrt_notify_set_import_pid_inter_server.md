---
type: API
title: aclrtNotifySetImportPidInterServer
description: 设置共享 Notify 的进程白名单。仅针对 Atlas A3 超节点产品，且仅 A3 平台支持。
tags:
- task.lookup
- topic.implementation.cross_process
- topic.implementation.synchronization
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
- a3
---
# aclrtNotifySetImportPidInterServer

## 功能说明

设置共享 Notify 的进程白名单。该接口仅针对 Atlas A3 超节点产品。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtNotifySetImportPidInterServerImpl`（notify.cpp:133）未对入参做空指针校验，直接通过 `rtNotifySetImportPidInterServer(notify, reinterpret_cast<const rtServerPid*>(serverPids), num)` 设置服务器级白名单。

## 函数原型

```c
aclError aclrtNotifySetImportPidInterServer(aclrtNotify notify, aclrtServerPid *serverPids, size_t num);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| notify | 输入 | 指定 Notify。必须先调用 [aclrtNotifyGetExportKey](aclrt_notify_get_export_key.md) 获取共享名称。 |
| serverPids | 输入 | 白名单信息数组，参见 aclrtServerPid。 |
| num | 输入 | serverPids 数组的大小。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 该接口仅针对 Atlas A3 超节点产品。