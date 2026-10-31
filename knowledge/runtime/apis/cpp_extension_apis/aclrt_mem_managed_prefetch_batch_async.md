---
type: API
title: aclrtMemManagedPrefetchBatchAsync
description: "C++ 模板批量预取 UVM，支持全部内存共用一个位置或按索引分组指定位置；完成需同步 Stream。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.data_movement
- topic.implementation.api_layer.cpp_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/26_cpp_extension_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt_api.h
  role: header
source_headers:
- include/external/acl/acl_rt_api.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- a2
---

# aclrtMemManagedPrefetchBatchAsync

## 功能说明

实现统一虚拟内存（Unified Virtual Memory, UVM）的批量预取。
本接口操作的内存必须是通过[aclrtMemAllocManaged](aclrt_mem_alloc_managed.md)接口分配的。本接口是异步接口，调用接口成功仅表示任务下发成功，不表示任务执行成功，调用本接口后，需调用同步等待接口（例如，aclrtSynchronizeStream）确保内存预取的任务已执行完成。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtMemManagedPrefetchBatchAsync。

## 函数原型

```cpp
template <typename T>
aclError aclrtMemManagedPrefetchBatchAsync(const T **ptrs, size_t *sizes, size_t count, aclrtMemManagedLocation prefetchLoc, uint64_t flags, aclrtStream stream)

template <typename T>
aclError aclrtMemManagedPrefetchBatchAsync(const T **ptrs, size_t *sizes, size_t count, aclrtMemManagedLocation *prefetchLocs, size_t *prefetchLocIdxs, size_t numPrefetchLocs, uint64_t flags, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptrs | 输入 | 待预取的内存地址数组，每个地址的范围都必须在UVM内存范围之内，即[0x90000000000ULL, 0x90000000000ULL+3TB)。 |
| sizes | 输入 | 内存预取长度数组，用于存放每一段要预取的UVM内存长度，单位Byte。每段长度都要求2MB对齐，取值范围为(0, 3TB]。 |
| count | 输入 | ptrs和sizes数组的长度。 |
| prefetchLoc | 输入 | 物理内存的位置信息，每个位置信息都包含id和type两个成员。针对所有待预取的内存，使用同一个物理内存的位置信息<br>类型定义请参见aclrtMemManagedLocation。 |
| prefetchLocs | 输入 | 物理内存的位置信息数组，每个位置信息都包含id和type两个成员。针对每一段待预取的内存，使用相应的物理内存的位置信息<br>类型定义请参见aclrtMemManagedLocation。 |
| prefetchLocIdxs | 输入 | 物理内存预取信息索引数组，用于指定prefetchLocs数组中的每个物理地址适用的预取范围。对于prefetchLocs[k]指定的物理地址，将预取ptrs数组中从第prefetchLocIdxs[k]个下标到第prefetchLocIdxs[k+1] – 1个下标指向元素的UVM内存地址，同时对于prefetchLocs[numPrefetchLocs -1]指定的物理地址，将预取ptrs数组中从第prefetchLocIdxs[numPrefetchLocs -1]个下标到第count - 1个下标指向元素的UVM内存地址。 |
| numPrefetchLocs | 输入 | prefetchLocs和prefetchLocIdxs数组的长度。 |
| flags | 输入 | 预留参数。当前固定配置为0。 |
| stream | 输入 | 指定执行内存预取任务的stream。类型定义请参见aclrtStream。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

约束与C接口aclrtMemManagedPrefetchBatchAsync接口保持一致。
