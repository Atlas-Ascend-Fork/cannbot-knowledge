---
type: API
title: aclrtCreateBinary
description: 创建 aclrtBinary 类型的数据，用于描述算子二进制信息。此处的算子为使用Ascend C开发的自定义算子。
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

# aclrtCreateBinary

## 功能说明

创建 aclrtBinary 类型的数据，用于描述算子二进制信息。此处的算子为使用Ascend C开发的自定义算子。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 创建 rtDevBinary_t 对象，设置 data 和 length 后返回 reinterpret_cast<aclrtBinary>。

## 函数原型

```c
aclrtBinary aclrtCreateBinary(const void *data, size_t dataLen)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| data | 输入 | 存放算子二进制文件（*.o）数据的内存地址。EP形态下为Host内存，RC/Control CPU形态下为Device内存。 |
| dataLen | 输入 | 内存大小（Byte）。 |

## 返回值说明

返回 aclrtBinary 类型的指针。

## 约束说明

EP形态用Host内存，RC/Control CPU/IPV350形态用Device内存。
