---
type: API
title: aclrtMallocHostWithCfg
description: 申请 Host 锁页内存，支持通过 cfg 指定额外配置信息。
tags:
- task.lookup
- topic.implementation.memory_management
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
# aclrtMallocHostWithCfg

## 功能说明

申请 Host 锁页内存，支持通过 cfg 指定额外配置信息。

## 函数原型

```c
aclError aclrtMallocHostWithCfg(void **ptr, uint64_t size, aclrtMallocConfig *cfg)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输出 | 已分配内存的指针的指针 |
| size | 输入 | 申请内存的大小，单位 Byte，不能为 0 |
| cfg | 输入 | 内存配置信息，不指定时传 NULL |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 310P/310B RC/Control CPU 形态下 Host=Device，按普通页申请
