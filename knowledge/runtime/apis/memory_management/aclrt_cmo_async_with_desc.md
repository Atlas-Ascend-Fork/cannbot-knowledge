---
type: API
title: aclrtCmoAsyncWithDesc
description: "通过 CmoSetDesc 准备的 Device 描述符向 Stream 异步下发 Cache 预取，当前仅支持 PREFETCH，reserve 须为 NULL。"
tags:
- task.lookup
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
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- a3
- a2
---
# aclrtCmoAsyncWithDesc

## 功能说明

使用内存描述符异步操作 Device 上的 Cache 内存。

## 函数原型

```c
aclError aclrtCmoAsyncWithDesc(void *cmoDesc, aclrtCmoType cmoType, aclrtStream stream, const void *reserve)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| cmoDesc | 输入 | 已通过 [aclrtCmoSetDesc](aclrt_cmo_set_desc.md) 设置的描述符地址 |
| cmoType | 输入 | Cache 操作类型，当前仅支持 PREFETCH |
| stream | 输入 | 执行操作任务的 Stream |
| reserve | 输入 | 预留参数，固定传 NULL |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`3_memory_advanced/cache_maintenance/0_prefetch_strategy_comparison/prefetch_strategy_comparison.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/cache_maintenance/0_prefetch_strategy_comparison/prefetch_strategy_comparison.cpp#L121)
