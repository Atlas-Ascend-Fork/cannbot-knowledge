---
type: API
title: aclGetDeviceCapability
description: 查询对应 Device 的硬件规格大小。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/24_other_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_base_rt.h
  role: header
source_headers:
- include/external/acl/acl_base_rt.h
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

# aclGetDeviceCapability

## 功能说明

查询运行环境中对应 Device 的硬件规格大小（如 AI Core 数量、内存大小等），根据 aclDeviceInfo 类型返回。

## 函数原型

```c
aclError aclGetDeviceCapability(uint32_t deviceId, aclDeviceInfo deviceInfo, int64_t *value)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| deviceId | 输入 | Device ID |
| deviceInfo | 输入 | 硬件规格类型 |
| value | 输出 | 规格值 |

## 返回值说明

返回 0 表示成功，其他值表示失败。