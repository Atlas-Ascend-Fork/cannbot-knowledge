---
type: API
title: asc_datacache_preload
description: 从GM地址预加载数据到Data Cache，每次调用预加载一个Cache Line大小的数据。
tags:
- task.lookup
- topic.data_movement.memory_access
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_datacache_preload.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/c_api/cache_ctrl/cache_ctrl.h
---

# asc_datacache_preload

## 功能说明

从源地址所在的特定GM地址预加载数据到Data Cache中，每次调用只能预加载一个Cache Line大小的数据。

## 函数原型

```cpp
__aicore__ inline void asc_datacache_preload(__gm__ uint64_t* address, int64_t offset)
```

## 参数说明

**表1** 参数说明

|参数名|输入/输出|描述|
|------------|------------|-----------|
| address     | 输入     | 源操作数的起始地址。   |
| offset     | 输入     | 在源操作数上偏移offset大小开始加载数据，单位为Bytes。|

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

频繁调用此接口可能会导致保留栈拥塞，此时，该接口将被视为NOP指令，阻塞Scalar流水。因此不建议频繁调用此接口。

## 调用示例

```cpp
// 假设x为外部传入的地址，每个核计算16个数据，block_idx为内置变量，通过block_idx计算偏移实现多核间数据隔离
__gm__ float* x_gm = x + block_idx * 16;
int64_t cacheOffset = 0;
asc_datacache_preload(reinterpret_cast<__gm__ uint64_t*>(x_gm), cacheOffset);
```
