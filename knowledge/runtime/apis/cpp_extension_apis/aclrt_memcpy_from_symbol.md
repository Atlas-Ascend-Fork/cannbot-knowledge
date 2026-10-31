---
type: API
title: aclrtMemcpyFromSymbol
description: "C++ 模板按 __gm__ 变量名及偏移，将 Device 变量同步读到 Host；offset 与 count 之和须在变量范围内。"
tags:
- task.lookup
- topic.data_movement.data_copy
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
- '310p'
---

# aclrtMemcpyFromSymbol

## 功能说明

实现Device变量的数据到Host的同步内存复制。用于读取Device变量的数据。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtMemcpyFromSymbol。

## 函数原型

```cpp
template <typename T>
aclError aclrtMemcpyFromSymbol(void *dst, size_t dstMax, const T &symbol, size_t count,
                               size_t offset, aclrtMemcpyKind kind)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| dst | 输入 | 目的内存地址指针。 |
| dstMax | 输入 | 目标内存最大长度，单位Byte。需满足 dstMax ≥ count。 |
| symbol | 输入 | Device变量名。此处传入`__gm__`声明的变量名。 |
| count | 输入 | 内存复制的长度，单位Byte。需满足 offset + count ≤ Device变量大小，Device变量大小可通过 [aclrtGetSymbolSize](aclrt_get_symbol_size.md)接口查询获取。 |
| offset | 输入 | Device变量地址偏移，单位Byte。需满足 offset + count ≤ Device变量大小，Device变量大小可通过 [aclrtGetSymbolSize](aclrt_get_symbol_size.md)接口查询获取。 |
| kind | 输入 | 拷贝类型，类型定义请参见aclrtMemcpyKind。本接口仅支持ACL_MEMCPY_DEVICE_TO_HOST和ACL_MEMCPY_DEFAULT。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

同[aclrtGetSymbolAddress](aclrt_get_symbol_address.md)接口约束说明。
