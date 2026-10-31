---
type: API
title: aclrtMemcpyBatch
description: "C++ 批量同步复制模板，调用 aclrtMemcpyBatchV2；支持统一或分组属性，无失败下标输出参数。"
tags:
- task.lookup
- topic.data_movement.data_copy
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
- '950'
- a3
- a2
---

# aclrtMemcpyBatch

## 功能说明

实现批量内存复制。
本接口中的Host内存支持锁页内存（例如通过aclrtMallocHost接口申请的内存）、非锁页内存（通过malloc接口申请的内存）。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtMemcpyBatchV2。

## 函数原型

```cpp
template <typename T, typename U>
aclError aclrtMemcpyBatch(T **dsts, size_t *destMaxs, U **srcs, size_t *sizes, size_t numBatches, aclrtMemcpyBatchAttr attr)

template <typename T, typename U>
aclError aclrtMemcpyBatch(T **dsts, size_t *destMaxs, U **srcs, size_t *sizes, size_t numBatches, aclrtMemcpyBatchAttr *attrs, size_t *attrsIndexes, size_t numAttrs)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dsts | 输入 | 目的内存地址数组。 |
| destMaxs | 输入 | 内存复制最大长度数组，用于存放每一段要复制的内存的最大长度，单位Byte。 |
| srcs | 输入 | 源内存地址数组。 |
| sizes | 输入 | 内存复制长度数组，用于存放每一段要复制的内存大小，单位Byte。 |
| numBatches | 输入 | dsts、srcs和sizes数组的长度。 |
| attr | 输入 | 内存复制属性。针对所有内存，使用同一个内存复制属性。<br>类型定义请参见aclrtMemcpyBatchAttr。 |
| attrs | 输入 | 内存复制属性数组。针对每一段内存，使用对应的内存复制属性。<br>类型定义请参见aclrtMemcpyBatchAttr。 |
| attrsIndexes | 输入 | 内存复制属性索引数组，用于指定attrs数组中每个条目适用的复制范围。attrs[k]中指定的属性将应用于从attrsIndexes[k]到attrsIndexes[k+1] - 1的复制操作，同时attrs[numAttrs-1]将应用于从attrsIndexes[numAttrs-1]到numBatches - 1的复制操作。 |
| numAttrs | 输入 | attrs和attrsIndexes数组的长度。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

约束与C接口aclrtMemcpyBatchV2保持一致。
