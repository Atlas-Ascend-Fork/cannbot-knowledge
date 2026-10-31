---
type: API
title: aclrtSnapShotProcessUnlock
description: 解锁 Device 上的当前进程，解除运行时接口阻塞。试验特性。
tags:
- task.lookup
- topic.checkpointing
- topic.implementation.synchronization
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/21_snapshot_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-31T02:47:07Z'
platforms:
- '950'
- a3
- a2
---

# aclrtSnapShotProcessUnlock

## 功能说明

解锁 Device 上的当前进程，解除运行时接口的阻塞调用。调用前需处于 LOCKED 或 BACKED_UP 状态，调用后变为 RUNNING 状态。

内部行为（固定 commit 源码结论）：参数校验后调用 `rtSnapShotProcessUnlock()`。

## 函数原型

```c
aclError aclrtSnapShotProcessUnlock(int pid, void* reserve)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| pid | 输入 | 进程 ID，当前只支持当前进程 |
| reserve | 输入 | 预留参数，必须传 NULL |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 本接口为试验特性，后续版本可能变更，不支持应用于生产环境中。
