---
type: API
title: aclrtSynchronizeStream
description: "C++ 带 timeout 的 Stream 同步封装，调用 aclrtSynchronizeStreamWithTimeout；-1 永久等待，正值为毫秒超时。"
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
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/06_stream_management.md
  role: supporting
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

# aclrtSynchronizeStream

## 功能说明

阻塞Host侧当前线程直到指定Stream中的所有任务都完成。同时，本接口支持用户设置超时时间，当应用程序异常时可根据所设置的超时时间自行退出。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtSynchronizeStreamWithTimeout。

固定头文件直接将参数转交给 [aclrtSynchronizeStreamWithTimeout](../stream_management/aclrt_synchronize_stream_with_timeout.md)；本卡的平台范围依据该 C 接口在同一固定提交中的产品支持声明，版本或封装实现变化后需重新核对。

## 函数原型

```cpp
aclError aclrtSynchronizeStream(aclrtStream stream, int32_t timeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定需要完成所有任务的Stream。类型定义请参见aclrtStream。 |
| timeout | 输入 | 接口的超时时间。<br>取值说明如下：<br>  - -1：表示永久等待；<br>  - >0：配置具体的超时时间，单位是毫秒。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
