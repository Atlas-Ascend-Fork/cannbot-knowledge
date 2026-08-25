---
type: API
title: asc_ldcg（内存访问函数）
description: 从L2 Cache加载缓存的数据，如果缓存命中，则直接返回数据。L2 Cache与Global Memory之间的数据一致性由硬件保证。若未命中，则从Global
  Memory地址预加载数据缓存至L2 Cache，并返回数据。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/memory_access_functions/asc_ldcg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_ldcg

从 L2 Cache 加载数据的函数。若 L2 Cache 命中则直接返回，未命中则从 Global Memory 读取并缓存到 L2 Cache。L2 Cache 与 Global Memory 间一致性由硬件保证。不会写入 Data Cache。

函数原型支持 30+ 种标量和向量类型的重载，包括 long、int、short、char、float、half、bfloat16_t 及对应的 unsigned 和向量类型（int2/int4/float2/float4 等）。参数 address 为 Global Memory 地址，返回该地址对应类型的数据。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"；half/half2 需 "simt_api/asc_fp16.h"，bfloat16_t/bfloat16x2_t 需 "simt_api/asc_bf16.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景，混合编程时需使用 __gm__ 地址空间限定符。

<!-- cannbot:related:start -->
## 相关

- [L2CacheSplit](../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_split.md)（`explains`）：asc_ldcg（内存访问函数） 与《L2CacheSplit》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [Scalar读写数据](../../../guides/technical_appendix/concepts_and_terms/memory_access/scalar_read_write.md)（`explains`）：asc_ldcg（内存访问函数） 与《Scalar读写数据》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [设置合理的L2 CacheMode](../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_mode_config.md)（`explains`）：asc_ldcg（内存访问函数） 与《设置合理的L2 CacheMode》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [asc_dcci_entire](asc_dcci_entire.md)（`related`）：asc_dcci_entire 与《asc_ldcg（内存访问函数）》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [asc_stcg（内存访问函数）](asc_stcg.md)（`related`）：Ldcg 是对应缓存加载路径，组成 cache-aware 读写。
- [AscDcci](../../simd_api/c_api/cache_ctrl/asc_dcci.md)（`same_topic`）：asc_ldcg（内存访问函数） 与《AscDcci》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [AscLdca](asc_ldca.md)（`same_topic`）：Ldca 与 Ldcg 都加载 GM 数据，但 cache 层级策略不同。
- [AscLoadL2CacheMode](../../simd_api/c_api/enum/asc_load_l2_cache_mode.md)（`same_topic`）：asc_ldcg（内存访问函数） 与《AscLoadL2CacheMode》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [asc_dcci_single](asc_dcci_single.md)（`same_topic`）：asc_ldcg（内存访问函数） 与《asc_dcci_single》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [asc_stwt（内存访问函数）](asc_stwt.md)（`same_topic`）：asc_stwt（内存访问函数） 与《asc_ldcg（内存访问函数）》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [访存函数](memory_access_functions.md)（`same_topic`）：asc_ldcg（内存访问函数） 与《访存函数》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [访存函数简介（内存访问函数）](memory_access_functions_intro.md)（`same_topic`）：asc_ldcg（内存访问函数） 与《访存函数简介（内存访问函数）》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
<!-- cannbot:related:end -->
