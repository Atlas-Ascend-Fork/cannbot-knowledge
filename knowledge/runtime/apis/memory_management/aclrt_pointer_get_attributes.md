---
type: API
title: aclrtPointerGetAttributes
description: "查询指针所在位置、页表大小等内存属性；禁止传入 HostRegister 映射得到的 Device 地址。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.data_movement.memory_access
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-05_unified_addressing.md
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
# aclrtPointerGetAttributes

## 功能说明

获取内存属性信息，包括位置、页表大小等。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtPointerGetAttributesImpl 调用 rtPointerGetAttributes 获取底层信息。

## 函数原型

```c
aclError aclrtPointerGetAttributes(const void *ptr, aclrtPtrAttributes *attributes)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | 内存地址（不允许传入 [aclrtHostRegister](aclrt_host_register.md) 映射的 Device 地址） |
| attributes | 输出 | 内存属性信息 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。
