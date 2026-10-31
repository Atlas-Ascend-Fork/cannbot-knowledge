---
type: API
title: aclrtValueWait
description: "向 Stream 异步下发内存值等待，按 GEQ、EQ、AND 或 NOR 条件比较 Device 地址中的值，满足条件后解除流阻塞。"
tags:
- task.lookup
- topic.data_movement.memory_access
- topic.implementation.synchronization
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-09_stream_memory_operation.md
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
- a3
- a2
---
# aclrtValueWait

## 功能说明

等待指定内存中的数据满足条件后解除阻塞。异步接口。

## 函数原型

```c
aclError aclrtValueWait(void* devAddr, uint64_t value, uint32_t flag, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devAddr | 输入 | Device 侧内存地址 |
| value | 输入 | 比较值 |
| flag | 输入 | 比较方式：GEQ/EQ/AND/NOR |
| stream | 输入 | 执行任务的 Stream，支持 NULL |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/9_multistream_sync_memory/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/9_multistream_sync_memory/main.cpp#L30)
