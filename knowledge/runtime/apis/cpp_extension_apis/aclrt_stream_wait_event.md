---
type: API
title: aclrtStreamWaitEvent
description: "C++ 三参数 Event 等待封装，调用 aclrtStreamWaitEventWithTimeout；异步阻塞指定 Stream，timeout 为 0 表示不超时。"
tags:
- task.lookup
- topic.implementation.synchronization
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

# aclrtStreamWaitEvent

## 功能说明

阻塞指定Stream的运行，直到指定的Event完成。异步接口。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtStreamWaitEventWithTimeout。

## 函数原型

```cpp
aclError aclrtStreamWaitEvent(aclrtStream stream, aclrtEvent event, int32_t timeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定Stream。类型定义请参见aclrtStream。<br>多Stream同步等待场景下，例如，Stream2等待Stream1的场景，此处配置为Stream2。 |
| event | 输入 | 需等待的Event。类型定义请参见aclrtEvent。 |
| timeout | 输入 | 超时时间。<br>取值说明如下：<br>  - 0：表示永不超时。<br>  - >0：用于配置具体的超时时间，单位是毫秒。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
