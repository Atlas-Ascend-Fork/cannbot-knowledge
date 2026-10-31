---
type: API
title: aclrtHostMemMapCapabilities
description: 查询硬件驱动加速器是否支持访问通过 aclrtHostRegister 注册的内存。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.data_movement.memory_access
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-02_host_memory_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtHostMemMapCapabilities

## 功能说明

查询硬件驱动加速器是否支持访问通过 [aclrtHostRegister](aclrt_host_register.md) 注册的内存。

## 函数原型

```c
aclError aclrtHostMemMapCapabilities(uint32_t deviceId, aclrtHacType hacType, aclrtHostMemMapCapability *capabilities)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID |
| hacType | 输入 | HAC 类型，见 aclrtHacType |
| capabilities | 输出 | 是否支持访问注册内存，见 aclrtHostMemMapCapability |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。
