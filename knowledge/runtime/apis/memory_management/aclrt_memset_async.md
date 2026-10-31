---
type: API
title: aclrtMemsetAsync
description: 下发到 Stream 的内存填充；锁页内存下为异步、非锁页 Host 内存下同步返回。
tags:
- task.lookup
- topic.data_movement.memory_access
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-03_memory_copy_and_set.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-30T07:38:42Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtMemsetAsync

## 功能说明

异步初始化内存为指定值。

## 函数原型

```c
aclError aclrtMemsetAsync(void *devPtr, size_t maxCount, int32_t value, size_t count, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输入 | 内存起始地址指针 |
| maxCount | 输入 | 内存最大长度，单位 Byte |
| value | 输入 | 设置的值 |
| count | 输入 | 需设置为指定值的内存长度，单位 Byte |
| stream | 输入 | 指定执行任务的 Stream |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 锁页内存下异步；非锁页 Host 内存下同步返回
- Host 内存非锁页可能导致未定义行为

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/model_ri/5_reusable_buffer_reset/reusable_buffer_reset.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/5_reusable_buffer_reset/reusable_buffer_reset.cpp#L62)
