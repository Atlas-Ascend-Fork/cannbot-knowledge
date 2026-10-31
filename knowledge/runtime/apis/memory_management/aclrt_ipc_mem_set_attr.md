---
type: API
title: aclrtIpcMemSetAttr
description: "按 IPC key 设置共享内存的访问链路属性；950 使用 UB，A3 使用 SIO/HCCS，须按产品选择属性值。"
tags:
- task.lookup
- topic.implementation.cross_process
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-07_IPC_memory_sharing.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- a3
---
# aclrtIpcMemSetAttr

## 功能说明

设置 IPC 共享内存的属性信息。

## 函数原型

```c
aclError aclrtIpcMemSetAttr(const char *key, aclrtIpcMemAttrType type, uint64_t attr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| key | 输入 | 共享内存 key |
| type | 输入 | 内存映射类型，当前仅支持 ACL_RT_IPC_MEM_ATTR_ACCESS_LINK |
| attr | 输入 | 属性值（950 支持 UB 路径，A3 支持 SIO/HCCS） |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 950 和 A3 支持的 attr 取值不同
