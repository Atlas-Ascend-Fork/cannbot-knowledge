---
type: API
title: aclrtMemMapSelectedLink
description: 将虚拟地址映射到另一虚拟地址对应的物理地址，可选择 HCCS/SIO 链路。
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-04_virtual_memory_management.md
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
- a3
---
# aclrtMemMapSelectedLink

## 功能说明

将虚拟地址映射到另一虚拟地址对应的物理地址，可选择 HCCS/SIO 链路。

## 函数原型

```c
aclError aclrtMemMapSelectedLink(void *virPtrDst, size_t size, void *virPtrSrc, uint32_t linkIdx)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| virPtrDst | 输入 | 待映射的虚拟内存地址（需提前预留） |
| size | 输入 | 虚拟内存大小 |
| virPtrSrc | 输入 | 已与物理内存建立映射的虚拟内存地址 |
| linkIdx | 输入 | 链路标识：0=SIO，1=HCCS |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- virPtrDst 不支持偏移后传入
