---
type: API
title: aclrtSubscribeHostFunc
description: "为 IPV350 的 CPU 算子调度注册用户创建的回调处理线程；每条 Stream 只能注册一个线程，一线程可服务多流。"
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
updated_at: "2026-10-30T08:26:15Z"
platforms: []
---

# aclrtSubscribeHostFunc

## 功能说明

注册处理 Stream 上回调函数的线程（由用户自行创建）。用于 IPV350 上 CPU 算子调度场景。

## 函数原型

```c
aclError aclrtSubscribeHostFunc(uint64_t hostFuncThreadId, aclrtStream exeStream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| hostFuncThreadId | 输入 | 指定线程 ID |
| exeStream | 输入 | 指定 Stream（不支持 NULL） |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 可给多个 Stream 注册同一个线程。
- 不支持给同一 Stream 注册多个线程。