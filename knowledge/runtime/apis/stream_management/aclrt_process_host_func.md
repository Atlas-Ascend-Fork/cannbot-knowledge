---
type: API
title: aclrtProcessHostFunc
description: "在用户创建并经 SubscribeHostFunc 注册的线程中等待、处理 Host 回调；timeout 以毫秒计，-1 为无限等待。"
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

# aclrtProcessHostFunc

## 功能说明

等待指定时间后触发回调处理，由 [aclrtSubscribeHostFunc](aclrt_subscribe_host_func.md) 指定的线程处理回调。线程由用户自行创建，在线程函数内调用本接口。

## 函数原型

```c
aclError aclrtProcessHostFunc(int32_t timeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| timeout | 输入 | 超时时间(ms)，-1 无限等待，>0 等待指定时间 |

## 返回值说明

返回 0 表示成功，其他值表示失败。