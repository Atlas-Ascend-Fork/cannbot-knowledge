---
type: API
title: aclrtPointerGetAttributes
description: "C++ 模板查询指针的 Host/Device 位置、页表大小等属性；不能传 Host 注册映射得到的 Device 地址。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.data_movement.memory_access
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

# aclrtPointerGetAttributes

## 功能说明

获取内存属性信息，包括内存是位于Host还是Device、页表大小等信息。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtPointerGetAttributes。

## 函数原型

```cpp
template <typename T>
aclError aclrtPointerGetAttributes(const T *ptr, aclrtPtrAttributes *attributes)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | 内存地址。<br>此处不允许传入通过aclrtHostRegister接口映射的Device地址，也不允许传入通过aclrtHostGetDevicePointer接口获取的Device地址，否则会导致未定义行为。 |
| attributes | 输出 | 内存属性信息。类型定义请参见aclrtPtrAttributes。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
