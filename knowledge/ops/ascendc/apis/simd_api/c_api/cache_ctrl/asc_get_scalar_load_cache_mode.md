---
type: API
title: asc_get_scalar_load_cache_mode
description: 读取当前标量读（load）路径的L2 Cache管理策略，并返回asc_load_l2_cache_mode枚举值。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_get_scalar_load_cache_mode.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/c_api/cache_ctrl/cache_ctrl.h
---

# asc_get_scalar_load_cache_mode

## 功能说明

读取当前标量读（load）路径的L2 Cache管理策略，并返回[asc_load_l2_cache_mode](../defs/enum/asc_load_l2_cache_mode.md)枚举值。

常用于临时切换策略前保存原配置，或在设置后做回读校验。

## 函数原型

```c
__aicore__ inline asc_load_l2_cache_mode asc_get_scalar_load_cache_mode()
```

## 参数说明

无

## 返回值说明

当前标量load路径的L2 Cache管理策略，类型为[asc_load_l2_cache_mode](../defs/enum/asc_load_l2_cache_mode.md)。

## 流水类型

PIPE_S

## 约束说明

- 本接口仅反映标量load侧策略，与标量store侧以及向量搬运接口参数中的`l2_cache_mode`无关。

## 调用示例

场景：GM tiling表在tile循环内被多次标量读取（每tile读`length`与`offset`）；进入循环前查询并保存当前load策略，临时切换为`NORMAL_FIRST_VICTIM`，循环结束后恢复。若tiling只读一次，可改用`NOTALLOC_KEEP`或无需切换。

```cpp
__gm__ int32_t* tiling_gm;   // [tile_count, len[0..n-1], off[0..n-1]]
__gm__ half* src_gm;
__ubuf__ half* dst_ub;

// 查询并保存当前标量load策略
asc_load_l2_cache_mode old_mode = asc_get_scalar_load_cache_mode();
asc_set_scalar_cache_mode(asc_load_l2_cache_mode::NORMAL_FIRST_VICTIM);

int32_t tile_count = tiling_gm[0];
for (int32_t tile = 0; tile < tile_count; ++tile) {
    int32_t tile_len = tiling_gm[1 + tile];              // 每tile标量读GM
    int32_t tile_off = tiling_gm[1 + tile_count + tile]; // 每tile标量读GM
    asc_copy_gm2ub_align(dst_ub, src_gm + tile_off, tile_len * sizeof(half));
    // ... 向量计算 ...
}

// 恢复进入本段逻辑前的标量load策略
asc_set_scalar_cache_mode(old_mode);
```
