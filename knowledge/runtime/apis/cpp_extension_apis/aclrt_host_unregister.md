---
type: API
title: aclrtHostUnregister
description: "C++ 模板以原始 Host 指针取消内存注册，与 aclrtHostRegister 配对，内部调用同名 C 接口。"
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
- a3
- a2
---

# aclrtHostUnregister

## 功能说明

取消注册Host内存。
本接口与[aclrtHostRegister](aclrt_host_register.md)接口成对使用。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtHostUnregister。

## 函数原型

```cpp
template <typename T>
aclError aclrtHostUnregister(T *ptr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | Host侧内存地址。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
