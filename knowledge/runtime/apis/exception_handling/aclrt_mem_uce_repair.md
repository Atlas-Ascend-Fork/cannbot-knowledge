---
type: API
title: aclrtMemUceRepair
description: 修复内存UCE的错误虚拟地址。试验特性。
tags:
- task.lookup
- task.debugging
- topic.implementation.error_handling
- topic.memory
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/13_exception_handling.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/event.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-31T02:15:45Z'
platforms:
- '950'
- 'a3'
- 'a2'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtMemUceRepair

## 功能说明

修复内存UCE的错误虚拟地址。试验特性。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 校验 arraySize <= 128；校验每个元素的 reserved 字段必须为0；构造 rtMemUceInfo 后委托 `rtMemUceRepair(deviceId, &rtUceInfo)` 到 RTS 层。

## 函数原型

```c
aclError aclrtMemUceRepair(int32_t deviceId, aclrtMemUceInfo *memUceInfoArray, size_t arraySize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID。 |
| memUceInfoArray | 输入 | aclrtMemUceInfo数组的指针。 |
| arraySize | 输入 | 传入数组的长度。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

- 本接口为试验特性，后续版本可能变更，不支持应用于生产环境中。
