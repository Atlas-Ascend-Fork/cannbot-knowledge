---
type: API
title: aclrtMemcpyBatchAsyncV2
description: 实现批量异步内存复制，不返回失败下标。
tags:
- task.lookup
- topic.data_movement.data_copy
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
updated_at: '2026-10-30T10:11:53Z'
platforms:
- '950'
- a3
- a2
---
# aclrtMemcpyBatchAsyncV2

## 功能说明

实现批量异步内存复制，不返回失败下标。

## 函数原型

```c
aclError aclrtMemcpyBatchAsyncV2(void **dsts, size_t *destMaxs, void **srcs, size_t *sizes, size_t numBatches, aclrtMemcpyBatchAttr *attrs, size_t *attrsIndexes, size_t numAttrs, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dsts | 输入 | 目的内存地址数组 |
| destMaxs | 输入 | 内存复制最大长度数组 |
| srcs | 输入 | 源内存地址数组 |
| sizes | 输入 | 内存复制长度数组 |
| numBatches | 输入 | 数组长度 |
| attrs | 输入 | 内存复制属性数组，长度为 numAttrs |
| attrsIndexes | 输入 | 各组属性开始适用的复制项下标数组，长度为 numAttrs；具体作用范围见约束说明 |
| numAttrs | 输入 | attrs 和 attrsIndexes 两个数组的长度 |
| stream | 输入 | 指定执行复制任务的 Stream |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- Host 内存为非锁页内存时，复制完成后接口才返回；为锁页内存时，成功返回仅表示任务下发成功。需通过同步等待接口（例如 `aclrtSynchronizeStream`）确认复制完成，再在 Host 端使用复制结果或释放相关内存。
- 批次内的复制操作无序，不保证按数组元素顺序执行。
- 整个批次只能执行 Host→Device 或 Device→Host 中的一种方向，不支持混合方向或 Device→Device。
- `attrs` 和 `attrsIndexes` 的长度均为 `numAttrs`。对 `0 <= k < numAttrs - 1`，`attrs[k]` 作用于复制项 `attrsIndexes[k]` 至 `attrsIndexes[k + 1] - 1`；最后一组作用至 `numBatches - 1`。
- `attrsIndexes[0]` 必须为 `0`，各项严格递增，最后一项小于 `numBatches`，且 `numAttrs <= numBatches`。
- 例如 10 项复制中，前 6 项使用 `attrs[0]`、后 4 项使用 `attrs[1]` 时，应设置 `numAttrs=2`、`attrsIndexes={0,6}`。
- 与 [aclrtMemcpyBatchAsync](aclrt_memcpy_batch_async.md) 相比不再通过 failIndex 返回失败下标。
