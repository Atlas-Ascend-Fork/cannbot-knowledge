---
type: API
title: asc_stwt（内存访问函数）
description: 将指定数据存储到Global Memory的地址address中，并缓存至Data Cache和L2 Cache。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/memory_access_functions/asc_stwt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_stwt

存储数据到 Global Memory 并缓存至 Data Cache 和 L2 Cache。适用于写入后可能很快被当前核再次读取的场景。

函数原型支持 30+ 种标量和向量类型的重载，包括 long、int、short、char、float、half、bfloat16_t 及对应的 unsigned 和向量类型（int2/int4/float2/float4 等）。参数 address 为 Global Memory 地址，val 为源操作数。无返回值。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"；half/half2 需 "simt_api/asc_fp16.h"，bfloat16_t/bfloat16x2_t 需 "simt_api/asc_bf16.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景，混合编程时需使用 __gm__ 地址空间限定符。

<!-- cannbot:related:start -->
## 相关

- [DCacheAccess](../../../guides/operator_practice/simt_operator_optimization/memory_access/dcache_access.md)（`explains`）：asc_stwt（内存访问函数） 与《DCacheAccess》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [Scalar读写数据](../../../guides/technical_appendix/concepts_and_terms/memory_access/scalar_read_write.md)（`explains`）：asc_stwt（内存访问函数） 与《Scalar读写数据》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [设置合理的L2 CacheMode](../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_mode_config.md)（`explains`）：asc_stwt（内存访问函数） 与《设置合理的L2 CacheMode》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [AscDcci](../../simd_api/c_api/cache_ctrl/asc_dcci.md)（`same_topic`）：asc_stwt（内存访问函数） 与《AscDcci》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [AscLdca](asc_ldca.md)（`same_topic`）：asc_stwt（内存访问函数） 与《AscLdca》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [AscStoreL2CacheMode](../../simd_api/c_api/enum/asc_store_l2_cache_mode.md)（`same_topic`）：asc_stwt（内存访问函数） 与《AscStoreL2CacheMode》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [asc_dcci_entire](asc_dcci_entire.md)（`same_topic`）：asc_stwt（内存访问函数） 与《asc_dcci_entire》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [asc_dcci_single](asc_dcci_single.md)（`same_topic`）：asc_stwt（内存访问函数） 与《asc_dcci_single》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [asc_ldcg（内存访问函数）](asc_ldcg.md)（`same_topic`）：asc_stwt（内存访问函数） 与《asc_ldcg（内存访问函数）》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [asc_stcg（内存访问函数）](asc_stcg.md)（`same_topic`）：asc_stwt（内存访问函数） 与《asc_stcg（内存访问函数）》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [访存函数](memory_access_functions.md)（`same_topic`）：asc_stwt（内存访问函数） 与《访存函数》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [访存函数简介（内存访问函数）](memory_access_functions_intro.md)（`same_topic`）：asc_stwt（内存访问函数） 与《访存函数简介（内存访问函数）》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
<!-- cannbot:related:end -->
