---
type: API
title: AscIcachePreload
description: 从指令所在GM地址预加载指令到ICache中，支持配置预取长度。
tags:
- task.lookup
- topic.data_movement.memory_access
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_icache_preload.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
---

# asc_icache_preload

## 功能说明

从指令所在GM地址预加载数据到对应的cacheline中。

开发者手动调用该接口，能够从指令所在GM地址预加载指令到ICache中。

## 函数原型

```cpp
__aicore__ inline void asc_icache_preload(const void* addr, int64_t prefetch_len)
```

## 参数说明

**表1** 参数说明

| 参数名 | 输入/输出 | 描述 |
| :--- | :--- | :--- |
| addr | 输入 | 预加载数据的地址。 |
| prefetch_len | 输入 | 预加载数据的长度，单位为2K Byte，取值需满足 $\text{prefetch\_len} < \dfrac{\text{ICache大小}}{2K}$。其中，AIC和AIV的ICache大小分别为32KB和16KB。 |

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

prefetch_len参数单位为2K Byte，取值需满足 $\text{prefetch\_len} < \dfrac{\text{ICache大小}}{2K}$。其中，AIC和AIV的ICache大小分别为32KB和16KB。

## 调用示例

```cpp
int64_t prefetch_length = 7;
int64_t pc = asc_get_program_counter() & 0xFFFFFFFFFFFF;
asc_icache_preload(reinterpret_cast<void *>(pc), prefetch_length);
```
