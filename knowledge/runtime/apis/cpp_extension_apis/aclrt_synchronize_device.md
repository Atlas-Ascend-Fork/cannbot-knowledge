---
type: API
title: aclrtSynchronizeDevice
description: "C++ 带 timeout 的 Device 同步封装，阻塞当前 Host 线程等待当前 Context 对应 Device；-1 永久等待，正值以毫秒计。"
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

# aclrtSynchronizeDevice

## 功能说明

阻塞当前线程，直到与当前线程绑定的Context所对应的Device完成运算。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtSynchronizeDeviceWithTimeout。

## 函数原型

```cpp
aclError aclrtSynchronizeDevice(int32_t timeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| timeout | 输入 | 接口的超时时间。<br>取值说明如下：<br>  - -1：表示永久等待；<br>  - >0：配置具体的超时时间，单位是毫秒。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
