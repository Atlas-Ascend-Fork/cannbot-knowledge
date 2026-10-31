---
type: API
title: aclrtIpcMemImportPidInterServer
description: 批量设置 IPC 共享内存的进程白名单（超节点产品）。
tags:
- task.lookup
- topic.implementation.cross_process
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-07_IPC_memory_sharing.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- a3
---
# aclrtIpcMemImportPidInterServer

## 功能说明

批量设置 IPC 共享内存的进程白名单（超节点产品）。

## 函数原型

```c
aclError aclrtIpcMemImportPidInterServer(const char *key, aclrtServerPid *serverPids, size_t num)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| key | 输入 | 共享内存 key |
| serverPids | 输入 | 白名单信息数组 |
| num | 输入 | 数组大小 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 仅 A3 超节点产品支持
