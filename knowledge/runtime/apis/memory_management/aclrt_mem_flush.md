---
type: API
title: aclrtMemFlush
description: "将指定 DDR 地址范围的 Cache 数据写回 DDR 并置为无效；正文所述版本无需用户处理 CPU/NPU Cache 一致性。"
tags:
- task.lookup
- topic.data_movement.memory_access
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
# aclrtMemFlush

## 功能说明

将 Cache 中的数据刷新到 DDR 中，并将 Cache 内容设置为无效。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtMemFlushImpl 调用 rtMemFlush 实现。

## 函数原型

```c
aclError aclrtMemFlush(void *devPtr, size_t size)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输入 | 要 Flush 的 DDR 内存起始地址指针 |
| size | 输入 | 要 Flush 的 DDR 内存大小，单位 Byte，不能为 0 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 当前版本不需要用户处理 CPU 与 NPU 间的 Cache 一致性，无需调用该接口
