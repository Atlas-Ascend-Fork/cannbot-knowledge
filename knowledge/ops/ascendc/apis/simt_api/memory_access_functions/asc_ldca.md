---
type: API
title: AscLdca
description: 从Data Cache加载数据，未命中则尝试L2 Cache，均未命中则从Global Memory读取并缓存。默认访存底层实现与本接口一致。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/memory_access_functions/asc_ldca.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_ldca

从 Data Cache 加载数据的函数。优先从 Data Cache 读取，未命中则尝试 L2 Cache，均未命中则从 Global Memory 读取并缓存到 L2 Cache 和 Data Cache。L2 Cache 与 Global Memory 间一致性由硬件保证，Data Cache 与 Global Memory 间不保证。默认访存底层实现与本接口等价（dst[idx] = src[idx] 等价于 dst[idx] = asc_ldca(src + idx)）。

函数原型支持 30+ 种标量和向量类型的重载，包括 long、int、short、char、float、half、bfloat16_t 及对应的 unsigned 和向量类型（int2/int4/float2/float4 等）。参数 address 为 Global Memory 地址，返回该地址对应类型的数据。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"；half/half2 需 "simt_api/asc_fp16.h"，bfloat16_t/bfloat16x2_t 需 "simt_api/asc_bf16.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景，混合编程时需使用 __gm__ 地址空间限定符。

<!-- cannbot:related:start -->
## 相关

- [asc_ldcg（内存访问函数）](asc_ldcg.md)（`related`）：从 Data Cache 加载数据的函数。优先从 Data Cache 读取，未命中则尝试 L2 Cache，均未命中则从 Global Memory 读取并缓存到 L2 Cache 和 Data Cache。L2 Cache 与 Global Memory 间一致性由硬件保证，Data Cache 与 Global Memory 间不保证。默认访存底层实现与本接口等价（dst［idx］ = src［idx］ 等价于 dst［idx］ = asc_ldca(src + idx)）。；从 L2 Cache 加载数据的函数。若 L2 Cache 命中则直接返回，未命中则从 Global Memory 读取并缓存到 L2 Cache。L2 Cache 与 Global Memory 间一致性由硬件保证。不会写入 Data Cache。两页给出 SIMT 加载在 Data Cache 与仅 L2 Cache 间的直接策略选择，一致性与缓存污染差异影响访存实现。
<!-- cannbot:related:end -->
