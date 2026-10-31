---
type: API
title: aclrtMalloc
description: "C++ 模板申请 Device 内存，返回类型化指针，可指定 policy 和 cfg；内部调用 aclrtMallocWithCfg，首地址 64 字节对齐。"
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

# aclrtMalloc

## 功能说明

在Device上分配size大小的线性内存，并通过\*devPtr返回已分配内存的指针，且内存首地址64字节对齐。
使用本接口申请的内存，需要通过aclrtFree接口或aclrtFreeWithDevSync接口释放内存。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtMallocWithCfg。

## 函数原型

```cpp
template <typename T>
aclError aclrtMalloc(T **devPtr, size_t size, aclrtMallocConfig *cfg = nullptr)

template <typename T>
aclError aclrtMalloc(T **devPtr, size_t size, aclrtMemMallocPolicy policy, aclrtMallocConfig *cfg = nullptr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输出 | “Device上已分配内存的指针”的指针。 |
| size | 输入 | 申请内存的大小，单位Byte。<br>size不能为0。 |
| policy | 输入 | 内存分配规则。类型定义请参见aclrtMemMallocPolicy。<br>若配置的内存分配规则超出aclrtMemMallocPolicy取值范围，size≥2MB时，按大页申请内存，否则按普通页申请内存。 |
| cfg | 输入 | 内存配置信息。类型定义请参见aclrtMallocConfig。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
