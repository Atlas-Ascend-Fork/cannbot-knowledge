---
type: API
title: aclrtCheckMemType
description: "批量检查 Device 地址是否匹配指定分配类型，支持 DEV、DVPP、RSVD 类型组合，输出 1 或 0 的匹配结果。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.memory
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-01_device_memory_malloc_and_free.md
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
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtCheckMemType

## 功能说明

检查 Device 内存地址的分配类型。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtCheckMemTypeImpl 检查各地址对应的底层内存类型并与 memType 比较。

## 函数原型

```c
aclError aclrtCheckMemType(void** addrList, uint32_t size, uint32_t memType, uint32_t *checkResult, uint32_t reserve)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| addrList | 输入 | Device 内存地址数组 |
| size | 输入 | addrList 数组大小 |
| memType | 输入 | 期望的内存类型，支持 ACL_RT_MEM_TYPE_DEV / DVPP / RSVD 位或 |
| checkResult | 输出 | 匹配结果：1=匹配，0=不匹配 |
| reserve | 输入 | 预留，固定配置为 0 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 950 系列不再有单独的 DVPP Device 内存类型
