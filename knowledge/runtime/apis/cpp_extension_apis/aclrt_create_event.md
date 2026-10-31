---
type: API
title: aclrtCreateEvent
description: "C++ 双参数 Event 创建封装，调用 aclrtCreateEventExWithFlag；由 flag 选择计时、同步或 IPC，资源不受硬件数量限制。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.cross_process
- topic.implementation.api_layer.cpp_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/26_cpp_extension_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt_api.h
  role: header
source_headers:
- include/external/acl/acl_rt_api.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclrtCreateEvent

## 功能说明

创建带flag的Event，不同flag的Event用于不同的功能。支持创建Event时携带多个flag（按位进行或操作），从而同时启用对应flag的功能。创建Event时，Event资源不受硬件限制。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtCreateEventExWithFlag。

## 函数原型

```cpp
aclError aclrtCreateEvent(aclrtEvent *event, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输出 | Event的指针。类型定义请参见aclrtEvent。 |
| flag | 输入 | Event指针的flag。<br>flag为bitmap，支持将flag设置为单个宏、或者对多个宏进行或操作。<br>当前支持将flag设置为如下宏：<br>  - ACL_EVENT_TIME_LINE：使用该bit表示创建的Event需要记录时间戳信息。注意：使用时间戳功能会影响Event相关接口的性能。<br>  - ACL_EVENT_SYNC：使用该bit表示创建的Event支持多Stream间的同步。<br>  - ACL_EVENT_CAPTURE_STREAM_PROGRESS：使用该bit表示创建的Event用于跟踪stream的任务执行进度。<br>  - ACL_EVENT_IPC：使用该bit表示创建的Event用于进程间通信，详细说明请参见aclrtIpcGetEventHandle。注意：Ascend 950DT上不支持使用本flag创建Event；本flag不支持与其他flag进行位或操作；本flag创建出来的Event不支持在以下接口或场景中使用：aclrtResetEvent、aclrtQueryEvent、aclrtQueryEventWaitStatus、aclrtEventElapsedTime、aclrtEventGetTimestamp、aclrtGetEventId、模型捕获场景（参见aclmdlRICaptureBegin中的说明），否则返回报错。<br><br><br>宏的定义如下：<br>#define ACL_EVENT_TIME_LINE 0x00000008U<br>#define ACL_EVENT_SYNC 0x00000001U<br>#define ACL_EVENT_CAPTURE_STREAM_PROGRESS 0x00000002U<br>#define ACL_EVENT_IPC 0x00000040U |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

约束与C接口aclrtCreateEventExWithFlag保持一致。
