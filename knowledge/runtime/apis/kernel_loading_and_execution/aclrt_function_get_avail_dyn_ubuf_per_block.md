---
type: API
title: aclrtFunctionGetAvailDynUbufPerBlock
description: 获取SIMT核函数每个Block可用的动态UB buffer最大大小。非SIMT核函数返回0。
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

# aclrtFunctionGetAvailDynUbufPerBlock

## 功能说明

获取SIMT核函数每个Block可用的动态UB buffer最大大小。非SIMT核函数返回0。


内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 校验 flags==0；委托 `rtFunctionGetAvailDynUbufPerBlock(func, flags, dynamicUbufSize)` 到 RTS 层。
## 函数原型

```c
aclError aclrtFunctionGetAvailDynUbufPerBlock(void *func, uint32_t flags, size_t *dynamicUbufSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| func | 输入 | 核函数句柄，不能为空。 |
| flags | 输入 | 预留参数，当前固定为0。 |
| dynamicUbufSize | 输出 | 每个Block可用的动态UB buffer大小（Byte）。不能为空。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明
