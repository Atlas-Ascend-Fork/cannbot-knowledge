---
type: API
title: aclrtGetSymbolSize
description: "C++ 模板按 __gm__ 变量名查询 Device 变量占用的字节数，用于 Ascend C 混合编译场景。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.memory
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

# aclrtGetSymbolSize

## 功能说明

获取Device变量占用的内存大小。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtGetSymbolSize。

## 函数原型

```cpp
template <typename T>
aclError aclrtGetSymbolSize(const T &symbol, size_t *size)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| symbol | 输入 | Device变量名。此处传入`__gm__`声明的变量名。 |
| size | 输出 | Device变量的大小，单位Byte。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

同[aclrtGetSymbolAddress](aclrt_get_symbol_address.md)接口约束说明。
