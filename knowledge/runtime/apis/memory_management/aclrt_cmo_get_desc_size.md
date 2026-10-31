---
type: API
title: aclrtCmoGetDescSize
description: 获取当前 Device 的 Cache 内存描述符大小。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.data_movement.memory_access
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-06_CMO_memory_operation.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- a3
- a2
---
# aclrtCmoGetDescSize

## 功能说明

获取当前 Device 的 Cache 内存描述符大小。

## 函数原型

```c
aclError aclrtCmoGetDescSize(size_t *size)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| size | 输出 | Cache 内存描述符大小，单位 Byte |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`3_memory_advanced/cache_maintenance/0_prefetch_strategy_comparison/prefetch_strategy_comparison.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/cache_maintenance/0_prefetch_strategy_comparison/prefetch_strategy_comparison.cpp#L83)
