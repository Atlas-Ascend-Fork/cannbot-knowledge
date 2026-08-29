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

- [DCacheAccess](../../../guides/operator_practice/simt_operator_optimization/memory_access/dcache_access.md)（`explains`）：存储数据到 Global Memory 并缓存到 L2 Cache，但不缓存至 Data Cache。适用于写入后不需要被当前核再次读取的场景，避免污染 Data Cache。；asc_stcg：存储数据时直接写入Global Memory，不经过DCache缓存，适用于写入GM后不会再从DCache读取的数据，避免输出数据占用DCache空间影响热点数据的缓存。；优化指南把焦点接口的缓存语义落到避免输出污染 DCache 的选型场景。
<!-- cannbot:related:end -->
