---
type: API
title: asc_dcci_single
description: 该接口用于刷新指定地址所在的Cache Line，保证数据读取时Cache的一致性。 在SIMT编程中，写入数据时会立即写入Global
  Memory，使其他核可见，因此不存在核间一致性问题。当从Global Memory读取数据时，该数据可能已被其他核修改，此时应使用dcci接口直接访问Global
  Memory，以获取最新数据。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/memory_access_functions/asc_dcci_single.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_dcci_single

刷新指定地址所在的 Cache Line，保证后续从 Global Memory 读取数据时 Cache 一致性。相比 asc_dcci_entire 仅刷新单条 Cache Line，适合轮询标志位等小范围刷新场景。

函数原型：inline void asc_dcci_single(void *dst)

参数 dst 为 Global Memory 地址。无返回值。输入必须为有效的 Global Memory 地址，否则不能保证刷新行为有效。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [AscDcci](../../simd_api/c_api/cache_ctrl/asc_dcci.md)（`related`）：AscDcci 与《asc_dcci_single》的实质衔接是：AscDcci 的 single/entire 变体与 C++ DataCacheCleanAndInvalid 操作同一 DCache；缓存概述、L2 驱逐故障和编译选项提供验证与尾开销决策。
- [AscLdca](asc_ldca.md)（`related`）：需要与其他代理保持可见时还需显式 cache clean/invalid，单纯 Ldca 不建立一致性。
- [asc_stcg（内存访问函数）](asc_stcg.md)（`related`）：跨代理可见性仍需 cache maintenance，Stcg 本身不等于一致性屏障。
- [访存函数简介（内存访问函数）](memory_access_functions_intro.md)（`related`）：数据可见性维护是 load/store 之外的关键操作。
- [asc_dcci_entire](asc_dcci_entire.md)（`same_topic`）：asc_dcci_entire 与《asc_dcci_single》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [asc_ldcg（内存访问函数）](asc_ldcg.md)（`same_topic`）：asc_ldcg（内存访问函数） 与《asc_dcci_single》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [asc_stwt（内存访问函数）](asc_stwt.md)（`same_topic`）：asc_stwt（内存访问函数） 与《asc_dcci_single》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
<!-- cannbot:related:end -->
