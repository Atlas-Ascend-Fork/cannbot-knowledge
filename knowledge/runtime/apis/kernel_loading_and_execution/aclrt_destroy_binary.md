---
type: API
title: aclrtDestroyBinary
description: 销毁通过 aclrtCreateBinary 创建的 aclrtBinary 数据。仅销毁 binary 数据，data 内存由用户自行释放。
tags:
- task.lookup
- topic.implementation.kernel_launch
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/14_Kernel_loading_and_execution.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/kernel.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtDestroyBinary

## 功能说明

销毁通过 [aclrtCreateBinary](aclrt_create_binary.md) 创建的 aclrtBinary 数据。仅销毁 binary 数据，data 内存由用户自行释放。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- `delete reinterpret_cast<rtDevBinary_t*>(binary)` 释放内部对象。

## 函数原型

```c
aclError aclrtDestroyBinary(aclrtBinary binary)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| binary | 输入 | 待销毁的 aclrtBinary 数据。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明
