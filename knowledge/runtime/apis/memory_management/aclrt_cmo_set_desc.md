---
type: API
title: aclrtCmoSetDesc
description: "在已申请的 Device 描述符内存中记录 Cache 操作地址和长度；先用 CmoGetDescSize 查询描述符大小。"
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
# aclrtCmoSetDesc

## 功能说明

设置 Cache 内存描述符，记录源地址和大小。

## 函数原型

```c
aclError aclrtCmoSetDesc(void *cmoDesc, void *src, size_t size)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| cmoDesc | 输入 | Cache 内存描述符地址指针（需先申请 Device 内存） |
| src | 输入 | 待操作的 Device 内存地址 |
| size | 输入 | 待操作的内存大小 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 需先调用 [aclrtCmoGetDescSize](aclrt_cmo_get_desc_size.md) 获取大小并申请 Device 内存

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`3_memory_advanced/cache_maintenance/0_prefetch_strategy_comparison/prefetch_strategy_comparison.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/cache_maintenance/0_prefetch_strategy_comparison/prefetch_strategy_comparison.cpp#L89)
