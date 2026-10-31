---
type: API
title: aclrtHostGetDevicePointer
description: "C++ 模板根据已注册的 Host 指针获取同类型的 Device 映射指针；预留 flag 必须为 0。"
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
---

# aclrtHostGetDevicePointer

## 功能说明

获取由[aclrtHostRegister](aclrt_host_register.md)接口注册映射的Device内存地址。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtHostGetDevicePointer。

## 函数原型

```cpp
template <typename T>
aclError aclrtHostGetDevicePointer(T *pHost, T **pDevice, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| pHost | 输入 | 通过[aclrtHostRegister](aclrt_host_register.md)接口注册映射的Host内存地址。 |
| pDevice | 输出 | Host内存映射成的Device内存地址。 |
| flag | 输入 | 预留参数，当前固定配置为0。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
