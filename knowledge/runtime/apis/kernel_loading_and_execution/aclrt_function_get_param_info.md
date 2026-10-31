---
type: API
title: aclrtFunctionGetParamInfo
description: 根据索引从核函数句柄获取参数信息（偏移和大小）。
tags:
- task.lookup
- topic.implementation.kernel_launch
- topic.implementation.resource_query
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

# aclrtFunctionGetParamInfo

## 功能说明

根据索引从核函数句柄获取参数信息（偏移和大小）。


内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 委托 `rtFunctionGetParamInfo(func, paramIndex, paramOffset, paramSize)` 到 RTS 层。
## 函数原型

```c
aclError aclrtFunctionGetParamInfo(const void *func, size_t paramIndex, size_t *paramOffset, size_t *paramSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| func | 输入 | 核函数句柄。 |
| paramIndex | 输入 | 参数索引，范围 [0, 参数数量-1)。 |
| paramOffset | 输出 | 参数在数据区中的偏移（Byte）。可为NULL。 |
| paramSize | 输出 | 参数大小（Byte）。可为NULL。paramOffset和paramSize不能同时为NULL。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明
