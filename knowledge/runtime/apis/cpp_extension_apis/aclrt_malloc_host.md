---
type: API
title: aclrtMallocHost
description: "C++ 模板申请 64 字节对齐的 Host 锁页内存，可传 cfg；内部调用 aclrtMallocHostWithCfg，配对 FreeHost 释放。"
tags:
- task.lookup
- topic.implementation.memory_management
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

# aclrtMallocHost

## 功能说明

申请Host内存（该内存是锁页内存），由系统保证内存首地址64字节对齐。
通过本接口申请的内存，需要通过aclrtFreeHost接口或aclrtFreeHostWithDevSync接口释放内存。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtMallocHostWithCfg。

## 函数原型

```cpp
template <typename T>
aclError aclrtMallocHost(T **hostPtr, size_t size, aclrtMallocConfig *cfg = nullptr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| hostPtr | 输出 | “已分配内存的指针”的指针。 |
| size | 输入 | 申请内存的大小，单位Byte。<br>size不能为0。 |
| cfg | 输入 | 内存配置信息。类型定义请参见aclrtMallocConfig。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
