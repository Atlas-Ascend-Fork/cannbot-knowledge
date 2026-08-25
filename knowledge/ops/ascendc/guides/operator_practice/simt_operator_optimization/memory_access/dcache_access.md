---
type: Guide
title: DCacheAccess
description: SIMT编程模式下通过不同访存函数为不同类型数据指定缓存策略，使热点数据优先驻留DCache，减少GM访问。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simt_operator_optimization/memory_access/dcache_access.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# DCache访问优化

【优先级】中
【描述】SIMT编程模式下，经由DCache访问Global Memory数据。当算子中存在多种不同访问模式的数据时，如仅遍历一次的输入数据与需要反复访问的热点数据，若不加区分，所有数据会共同竞争DCache空间，导致热点数据被其他数据挤出DCache，后续再次访问热点数据时需要从GM重新加载，增加访存时间。此时可以通过不同访存函数，为不同类型的数据指定不同的缓存策略，使热点数据优先驻留DCache，减少不必要的GM访问。
SIMT编程模式下提供以下访存函数：
- asc_ldcg：加载数据时从Global Memory加载，适用于仅遍历一次的输入数据，减少其对DCache空间的占用。
- asc_ldca：加载数据时优先从DCache加载，适用于需要频繁访问的热点数据（如查找表），确保热点数据常驻DCache，减少从Global Memory重新加载的次数。
- asc_stcg：存储数据时直接写入Global Memory，不经过DCache缓存，适用于写入GM后不会再从DCache读取的数据，避免输出数据占用DCache空间影响热点数据的缓存。
【样例介绍】以sin查表算子为例，使用查表法计算sin值，通过线性插值提高精度。输入数据长度为65536（256KB），sin查找表长度为8192（32KB）。算法实现中，每个线程根据输入值计算查找表索引，根据索引从sin表中读取对应位置及其后续位置的数据，通过线性插值得到结果。其中每个输入数据仅访问一次，属于非热点数据；sin查找表会被反复访问，属于热点数据。
【反例】所有数据使用默认方式加载，输入、输出和sin表数据共同竞争DCache空间。
上述实现中，input[idx]、sin_table[n]、sin_table[n+1]和output[idx]均使用默认方式访问Global Memory。输入数据虽然仅访问一次，但其加载时会占用DCache空间；输出数据写入后也可能驻留DCache。当输入和输出数据大量加载时，sin查找表的数据会被挤出DCache，导致后续线程查表时需要重新从Global Memory加载，增加DCache Read GM次数。
反例算子的性能数据如下：
Task Duration(us)：DCache Read GM(次)：DCache Read Vector(次)：DCache Write Vector(次)
56.82：5064：2048：6144
【正例】使用访存函数区分不同数据的缓存策略。

<!-- cannbot:related:start -->
## 相关

- [DataCachePreload](../../../../apis/simd_api/basic_api/cache_control/data_cache_preload.md)（`explains`）：DataCachePreload 与《DCacheAccess》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [asc_dcci_entire](../../../../apis/simt_api/memory_access_functions/asc_dcci_entire.md)（`explains`）：asc_dcci_entire 与《DCacheAccess》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [asc_stwt（内存访问函数）](../../../../apis/simt_api/memory_access_functions/asc_stwt.md)（`explains`）：asc_stwt（内存访问函数） 与《DCacheAccess》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [缓存控制](../../../../apis/simd_api/c_api/cache_ctrl/cache_control.md)（`explains`）：缓存控制 与《DCacheAccess》的实质衔接是：C 缓存控制页覆盖 DCache/ICache 预取与失效；系统缓存、缓存一致性、DCI 优化和无参清理编译失败补充作用域、目标对象及使用边界。
- [访存函数简介（内存访问函数）](../../../../apis/simt_api/memory_access_functions/memory_access_functions_intro.md)（`explains`）：DCache 策略依赖 asc_ldcg/asc_ldca/asc_stcg 等显式加载存储函数；接口导论解释缓存路径、写回与一致性，是实施优化的 API 依据。
- [MemoryAccessMerge](memory_access_merge.md)（`related`）：缓存驻留优化解决热点复用，访存合并解决 Warp 地址连续性；两者同时决定 GM/DCache 有效带宽，不能用其中一个代替另一个。
- [ShortVectorEfficiency](short_vector_efficiency.md)（`related`）：短向量能让一次搬运覆盖更多连续字节/Cache Line，与 DCache 策略组合可减少事务数并提升热点访问吞吐。
<!-- cannbot:related:end -->
