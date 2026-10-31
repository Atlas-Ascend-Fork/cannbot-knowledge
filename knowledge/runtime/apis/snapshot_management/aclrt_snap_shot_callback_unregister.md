---
type: API
title: aclrtSnapShotCallbackUnregister
description: 取消注册快照操作回调函数。试验特性。
tags:
- task.lookup
- topic.checkpointing
- topic.implementation.callback
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

# aclrtSnapShotCallbackUnregister

## 功能说明

取消注册回调函数。取消后对应快照阶段不再调用该回调。

内部行为（固定 commit 源码结论）：封装调用 `rtSnapShotCallbackUnregister(stage, callback)`。

## 函数原型

```c
aclError aclrtSnapShotCallbackUnregister(aclrtSnapShotStage stage, aclrtSnapShotCallBack callback)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| stage | 输入 | 快照阶段 |
| callback | 输入 | 待取消注册的回调函数指针 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 本接口为试验特性，后续版本可能变更，不支持应用于生产环境中。
