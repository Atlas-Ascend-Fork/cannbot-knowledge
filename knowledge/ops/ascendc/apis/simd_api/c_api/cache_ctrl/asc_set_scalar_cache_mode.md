---
type: API
title: asc_set_scalar_cache_mode
description: 配置标量单元访问Global Memory时的L2 Cache管理策略。接口通过修改CTRL寄存器对应比特域生效：
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_set_scalar_cache_mode.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/c_api/cache_ctrl/cache_ctrl.h
---

# asc_set_scalar_cache_mode

## 功能说明

配置标量单元访问Global Memory时的L2 Cache管理策略。接口通过修改CTRL寄存器对应比特域生效：

- 传入[asc_load_l2_cache_mode](../defs/enum/asc_load_l2_cache_mode.md)时，设置标量读（load）策略。
- 传入[asc_store_l2_cache_mode](../defs/enum/asc_store_l2_cache_mode.md)时，设置标量写（store）策略。

设置后，后续标量路径上的GM读写将按该策略访问L2 Cache，直至再次调用本接口修改。

## 函数原型

```c
__aicore__ inline void asc_set_scalar_cache_mode(asc_load_l2_cache_mode l2_cache_mode)
__aicore__ inline void asc_set_scalar_cache_mode(asc_store_l2_cache_mode l2_cache_mode)
```

## 参数说明

**表1** 参数说明

| 参数名 | 输入/输出 | 描述 |
| :--- | :--- | :--- |
| l2_cache_mode | 输入 | L2 Cache管理策略。load重载传入[asc_load_l2_cache_mode](../defs/enum/asc_load_l2_cache_mode.md)枚举值；store重载传入[asc_store_l2_cache_mode](../defs/enum/asc_store_l2_cache_mode.md)枚举值。 |

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

- 本接口仅影响**标量访存路径**的L2 Cache默认策略，不会修改向量搬运类接口（如[asc_copy_gm2ub_align](../vector_datamove/asc_copy_gm2ub_align/asc_copy_gm2ub_align_arch_3510.md)、[asc_copy_ub2gm_align](../vector_datamove/asc_copy_ub2gm_align/asc_copy_ub2gm_align_arch_3510.md)、[asc_ndim_copy_gm2ub](../vector_datamove/asc_ndim_copy_gm2ub.md)等）参数中的`l2_cache_mode`；二者相互独立。大块tile数据的L2 Cache优化应通过向量搬运入参配置，参见[L2 Cache Mode最佳实践样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/02_simd_c_api/02_features/00_data_movement/00_set_l2_cache_mode)。
- load与store策略分属CTRL不同比特域，设置其一不会覆盖另一侧已配置的值。

## 调用示例

- 场景A：标量load — `NORMAL_FIRST_VICTIM`+循环内重复读GM tiling表

动态tiling存放在GM上：`tiling_gm[0]`为`tile_count`，后续依次为各tile的`length`与`offset`。循环内每个tile都会标量读取tiling字段，同一tiling区域会被多次访问，适合启用L2复用。若tiling字段只读一次、后续不再访问，应改用`NOTALLOC_KEEP`或无需调用本接口。

```cpp
__gm__ int32_t* tiling_gm;   // [tile_count, len[0..n-1], off[0..n-1]]
__gm__ half* src_gm;
__ubuf__ half* dst_ub;

// SIMD_VF外：tiling表将在循环内被多次标量读取
asc_set_scalar_cache_mode(asc_load_l2_cache_mode::NORMAL_FIRST_VICTIM);

int32_t tile_count = tiling_gm[0];
for (int32_t tile = 0; tile < tile_count; ++tile) {
    int32_t tile_len = tiling_gm[1 + tile];              // 每tile标量读GM
    int32_t tile_off = tiling_gm[1 + tile_count + tile]; // 每tile标量读GM
    asc_copy_gm2ub_align(dst_ub, src_gm + tile_off, tile_len * sizeof(half));
    // 向量搬运的l2_cache_mode由asc_copy_gm2ub_align单独配置，见set_l2_cache_mode样例
    // ... 向量计算 ...
}
```

- 场景B：标量store — `NOTALLOC_CLEAN`+标量写GM

多核算子向GM统计counter做标量原子累加时，临时关闭标量写路径的L2分配，避免对控制字段产生不必要的Cache Line分配。

```cpp
__gm__ int32_t* counter_gm;  // GM上的多核共享计数器

asc_set_scalar_cache_mode(asc_store_l2_cache_mode::NOTALLOC_CLEAN);
asc_dcci_entire_all();       // 标量原子操作前保证DCache一致性
asc_atomic_add(counter_gm, 1);
```
