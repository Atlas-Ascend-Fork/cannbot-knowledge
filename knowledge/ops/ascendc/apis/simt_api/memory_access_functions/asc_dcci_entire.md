---
type: API
title: asc_dcci_entire
description: 该接口用于刷新核内的整个Data Cache，保证数据读取时Cache的一致性。 在SIMT编程中，写入数据时会立即写入Global Memory，使其他核可见，因此不存在核间一致性问题。当从Global
  Memory读取数据时，该数据可能已被其他核修改，此时应使用dcci接口直接访问Global Memory，以获取最新数据。 请注意，该接口耗时较大，性能敏感的场景慎用。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/memory_access_functions/asc_dcci_entire.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_dcci_entire

刷新核内整个 Data Cache，保证后续从 Global Memory 读取数据时 Cache 一致性。SIMT 编程中写入数据会立即写入 Global Memory 使其他核可见，但当读取的数据可能已被其他核修改时，需使用 dcci 接口刷新 Data Cache 以获取最新数据。

函数原型：inline void asc_dcci_entire(void *dst)

参数 dst 为 Global Memory 地址。无返回值。该接口耗时较大，性能敏感场景慎用。输入必须为有效的 Global Memory 地址，否则不能保证刷新行为有效。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [DCacheAccess](../../../guides/operator_practice/simt_operator_optimization/memory_access/dcache_access.md)（`explains`）：asc_dcci_entire 与《DCacheAccess》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [Scalar读写数据](../../../guides/technical_appendix/concepts_and_terms/memory_access/scalar_read_write.md)（`explains`）：asc_dcci_entire 与《Scalar读写数据》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [asc_ldcg（内存访问函数）](asc_ldcg.md)（`related`）：asc_dcci_entire 与《asc_ldcg（内存访问函数）》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [asc_stcg（内存访问函数）](asc_stcg.md)（`related`）：asc_dcci_entire 与《asc_stcg（内存访问函数）》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [AscDcci](../../simd_api/c_api/cache_ctrl/asc_dcci.md)（`same_topic`）：asc_dcci_entire 与《AscDcci》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [asc_dcci_single](asc_dcci_single.md)（`same_topic`）：asc_dcci_entire 与《asc_dcci_single》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [asc_dci（缓存控制）](../../simd_api/c_api/cache_ctrl/asc_dci.md)（`same_topic`）：asc_dcci_entire 与《asc_dci（缓存控制）》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [asc_stwt（内存访问函数）](asc_stwt.md)（`same_topic`）：asc_stwt（内存访问函数） 与《asc_dcci_entire》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [缓存控制](../../simd_api/c_api/cache_ctrl/cache_control.md)（`same_topic`）：asc_dcci_entire 与《缓存控制》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
<!-- cannbot:related:end -->
