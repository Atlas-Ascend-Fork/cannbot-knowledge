---
type: API
title: aclrtUnSubscribeHostFunc
description: 取消线程注册，Stream 上的回调不再由指定线程处理。
tags:
- task.lookup
- topic.implementation.callback
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/24_other_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms: []
---

# aclrtUnSubscribeHostFunc

## 功能说明

取消线程注册，配合 [aclrtSubscribeHostFunc](aclrt_subscribe_host_func.md) 使用。调用后 Stream 上的回调函数不再由指定线程处理。

## 函数原型

```c
aclError aclrtUnSubscribeHostFunc(uint64_t hostFuncThreadId, aclrtStream exeStream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| hostFuncThreadId | 输入 | 指定线程 ID |
| exeStream | 输入 | 指定 Stream（不支持 NULL） |

## 返回值说明

返回 0 表示成功，其他值表示失败。