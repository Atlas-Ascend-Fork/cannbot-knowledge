---
type: API
title: aclrtMemcpyToSymbolAsync
description: "C++ 模板按 __gm__ 变量名将 Host 数据写入 Device，指定偏移和 Stream；Host 锁页内存下异步，非锁页下同步返回。"
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

# aclrtMemcpyToSymbolAsync

## 功能说明

实现Host数据到Device变量的异步内存复制。用于向Device变量写入数据。
本接口中的Host内存支持锁页内存（例如通过aclrtMallocHost接口申请的内存）、非锁页内存（通过malloc接口申请的内存）。当Host内存是锁页内存时，本接口是异步接口，调用接口成功仅表示任务下发成功，不表示任务执行成功，调用本接口后，需调用同步等待接口（例如，aclrtSynchronizeStream）确保内存复制的任务已执行完成；当Host内存是非锁页内存时，本接口在内存复制任务完成后才返回。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtMemcpyToSymbolAsync。

## 函数原型

```cpp
template <typename T>
aclError aclrtMemcpyToSymbolAsync(const T &symbol, const void *src, size_t count, size_t offset,
                                  aclrtMemcpyKind kind, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| symbol | 输入 | Device变量名。此处传入`__gm__`声明的变量名。 |
| src | 输入 | 源内存地址指针。 |
| count | 输入 | 内存复制的长度，单位Byte。需满足 offset + count ≤ Device变量大小，Device变量大小可通过 [aclrtGetSymbolSize](aclrt_get_symbol_size.md)接口查询获取。 |
| offset | 输入 | Device变量地址偏移，单位Byte。需满足 offset + count ≤ Device变量大小，Device变量大小可通过 [aclrtGetSymbolSize](aclrt_get_symbol_size.md)接口查询获取。 |
| kind | 输入 | 拷贝类型，类型定义请参见aclrtMemcpyKind。本接口仅支持ACL_MEMCPY_HOST_TO_DEVICE和ACL_MEMCPY_DEFAULT。 |
| stream | 输入 | 指定执行内存复制任务的Stream。类型定义请参见aclrtStream。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

- 同[aclrtGetSymbolAddress](aclrt_get_symbol_address.md)接口约束说明。
- 本接口为异步接口，调用后需同步等待拷贝完成。
