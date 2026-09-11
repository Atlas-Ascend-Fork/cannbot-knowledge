---
type: API
title: asc_get_scalar_store_cache_mode
description: 读取当前标量写（store）路径的L2 Cache管理策略，并返回asc_store_l2_cache_mode枚举值。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_get_scalar_store_cache_mode.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/c_api/cache_ctrl/cache_ctrl.h
---

# asc_get_scalar_store_cache_mode

## 功能说明

读取当前标量写（store）路径的L2 Cache管理策略，并返回[asc_store_l2_cache_mode](../defs/enum/asc_store_l2_cache_mode.md)枚举值。

常用于临时切换策略前保存原配置，或在设置后做回读校验。

## 函数原型

```c
__aicore__ inline asc_store_l2_cache_mode asc_get_scalar_store_cache_mode()
```

## 参数说明

无

## 返回值说明

当前标量store路径的L2 Cache管理策略，类型为[asc_store_l2_cache_mode](../defs/enum/asc_store_l2_cache_mode.md)。

## 流水类型

PIPE_S

## 约束说明

- 本接口仅反映标量store侧策略，与标量load侧以及向量搬运接口参数中的`l2_cache_mode`无关。

## 调用示例

场景：与[asc_set_scalar_cache_mode](asc_set_scalar_cache_mode.md)场景B一致。多核算子通过[asc_atomic_add](../atomic/scalar_atomic/asc_atomic_add.md)向GM统计counter做标量原子累加；进入累加前查询并保存当前store策略，临时切换为`NOTALLOC_CLEAN`避免不必要的L2分配，累加结束后恢复原策略。

```cpp
__gm__ int32_t* counter_gm;  // GM上的多核共享计数器

// 查询并保存当前标量store策略
asc_store_l2_cache_mode old_mode = asc_get_scalar_store_cache_mode();
// 标量原子写GM控制字段，避免额外L2分配
asc_set_scalar_cache_mode(asc_store_l2_cache_mode::NOTALLOC_CLEAN);

asc_dcci_entire_all();  // 标量原子操作前保证DCache一致性
asc_atomic_add(counter_gm, 1);

// 恢复进入本段逻辑前的标量store策略
asc_set_scalar_cache_mode(old_mode);
```
