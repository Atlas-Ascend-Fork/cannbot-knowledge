---
type: API
title: aclplatformGetDeviceInfo
description: 查询 AI 处理器型号的硬件信息。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/24_other_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_platform.h
  role: header
source_headers:
- include/external/acl/acl_platform.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-30T07:10:24Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclplatformGetDeviceInfo

## 功能说明

查询对应 AI 处理器型号的硬件信息（如芯片名称、算力等），按 aclplatformDevInfo 类型返回字符串形式的结果。

## 函数原型

```c
aclError aclplatformGetDeviceInfo(aclplatformDevInfo infoType, char *value, uint32_t maxLen)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| infoType | 输入 | 硬件信息类型 |
| value | 输出 | 查询结果字符串缓冲区 |
| maxLen | 输入 | value 最大长度 |

## 返回值说明

返回 0 表示成功，其他值表示失败。