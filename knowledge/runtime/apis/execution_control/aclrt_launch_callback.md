---
type: API
title: aclrtLaunchCallback
description: 在Stream的任务队列中下发一个Host回调任务，系统内部在执行到该回调任务时，在Stream上注册的线程中执行回调函数。异步接口，需配合 aclrtSubscribeReport/aclrtProcessReport/aclrtUnSubscribeReport 使用。
tags:
- task.lookup
- topic.implementation.callback
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/12_execution_control.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/callback.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
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

# aclrtLaunchCallback

## 功能说明

在Stream的任务队列中下发一个Host回调任务，系统内部在执行到该回调任务时，在Stream上注册的线程中执行回调函数。异步接口，需配合 [aclrtSubscribeReport](aclrt_subscribe_report.md)/[aclrtProcessReport](aclrt_process_report.md)/[aclrtUnSubscribeReport](aclrt_un_subscribe_report.md) 使用。
## 函数原型

```c
aclError aclrtLaunchCallback(aclrtCallback fn, void *userData, aclrtCallbackBlockType blockType, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| fn | 输入 | 指定要增加的回调函数。函数原型：typedef void (*aclrtCallback)(void*userData) |
| userData | 输入 | 待传递给回调函数的用户数据的指针。 |
| blockType | 输入 | 指定回调任务是否阻塞本Stream上后续任务的执行。ACL_CALLBACK_NO_BLOCK 或 ACL_CALLBACK_BLOCK。 |
| stream | 输入 | 指定Stream。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

回调函数涉及共享资源（例如锁），不应调用资源申请/释放、Stream同步、Device同步、任务下发、任务终止等接口，否则可能导致错误或死锁。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp#L131)
