---
type: API
title: aclrtSetOpExecuteTimeOut
description: "C++ 双参数算子超时封装，调用 aclrtSetOpExecuteTimeOutV2；以微秒设置并返回实际生效值，任务自身超时优先。"
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

# aclrtSetOpExecuteTimeOut

## 功能说明

设置算子执行的超时时间，单位为微秒。如果算子下发时携带了超时时间，则该超时时间优先级高于本接口设置的超时时间。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtSetOpExecuteTimeOutV2。

## 函数原型

```cpp
aclError aclrtSetOpExecuteTimeOut(uint64_t timeout, uint64_t *actualTimeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| timeout | 输入 | 设置超时时间，单位为微秒。<br>将该参数设置为0时，表示使用最大超时时间。 |
| actualTimeout | 输出 | 返回实际生效的超时时间，单位为微秒。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

约束与C接口aclrtSetOpExecuteTimeOutV2保持一致。
