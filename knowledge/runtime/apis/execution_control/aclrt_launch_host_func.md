---
type: API
title: aclrtLaunchHostFunc
description: 在Stream的任务队列中下发Host回调任务，系统内部创建并注册线程执行回调，回调默认阻塞本Stream后续任务。异步接口。
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

# aclrtLaunchHostFunc

## 功能说明

在Stream的任务队列中下发Host回调任务，系统内部创建并注册线程执行回调，回调默认阻塞本Stream后续任务。异步接口。
## 函数原型

```c
aclError aclrtLaunchHostFunc(aclrtStream stream, aclrtHostFunc fn, void *args)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定执行回调任务的Stream。 |
| fn | 输入 | 指定回调函数。函数原型：typedef void (*aclrtHostFunc)(void*args) |
| args | 输入 | 待传递给回调函数的用户数据。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

回调函数不应调用资源申请/释放、Stream同步、Device同步、任务下发、任务终止等接口。与 [aclrtLaunchCallback](aclrt_launch_callback.md) 等接口不能对同一Stream混用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/callback/0_simple_callback/callback_sample.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/callback/0_simple_callback/callback_sample.cpp#L58)
- [`2_advanced_features/callback/1_callback_hostfunc/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/callback/1_callback_hostfunc/main.cpp#L42)
