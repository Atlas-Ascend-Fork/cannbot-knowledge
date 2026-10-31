---
type: API
title: aclplatformGetInstructionInfo
description: 根据核类型查询指定指令的相关属性信息。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.architecture
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

# aclplatformGetInstructionInfo

## 功能说明

根据核类型查询指定指令的相关属性信息。适用于查询当前 NPU 架构对特定指令的支持情况。

## 函数原型

```c
aclError aclplatformGetInstructionInfo(aclplatformCoreType type, const char *instruction, char *value, uint32_t maxLen)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| type | 输入 | 核类型 |
| instruction | 输入 | 指令名称（如 "Intrinsic_vexp"） |
| value | 输出 | 查询结果字符串缓冲区 |
| maxLen | 输入 | value 最大长度 |

## 返回值说明

返回 0 表示成功，其他值表示失败。