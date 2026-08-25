---
type: API
title: asc_stcg（内存访问函数）
description: 将指定数据存储到Global Memory的地址address中，并缓存到L2 Cache，但不缓存至Data Cache。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/memory_access_functions/asc_stcg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_stcg

存储数据到 Global Memory 并缓存到 L2 Cache，但不缓存至 Data Cache。适用于写入后不需要被当前核再次读取的场景，避免污染 Data Cache。

函数原型支持 30+ 种标量和向量类型的重载，包括 long、int、short、char、float、half、bfloat16_t 及对应的 unsigned 和向量类型（int2/int4/float2/float4 等）。参数 address 为 Global Memory 地址，val 为源操作数。无返回值。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"；half/half2 需 "simt_api/asc_fp16.h"，bfloat16_t/bfloat16x2_t 需 "simt_api/asc_bf16.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景，混合编程时需使用 __gm__ 地址空间限定符。

<!-- cannbot:related:start -->
## 相关

- [设置合理的L2 CacheMode](../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_mode_config.md)（`explains`）：L2 mode 指南解释 Stcg 写入 L2 的行为和适用场景。
- [AscLdca](asc_ldca.md)（`related`）：Stcg 是对应写路径，与 Ldca 组成读取/更新链。
- [asc_dcci_entire](asc_dcci_entire.md)（`related`）：asc_dcci_entire 与《asc_stcg（内存访问函数）》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [asc_dcci_single](asc_dcci_single.md)（`related`）：跨代理可见性仍需 cache maintenance，Stcg 本身不等于一致性屏障。
- [asc_ldcg（内存访问函数）](asc_ldcg.md)（`related`）：Ldcg 是对应缓存加载路径，组成 cache-aware 读写。
- [asc_stwt（内存访问函数）](asc_stwt.md)（`same_topic`）：asc_stwt（内存访问函数） 与《asc_stcg（内存访问函数）》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
<!-- cannbot:related:end -->
