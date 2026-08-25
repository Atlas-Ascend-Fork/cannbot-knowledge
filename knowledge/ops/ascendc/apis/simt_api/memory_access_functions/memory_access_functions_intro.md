---
type: API
title: 访存函数简介（内存访问函数）
description: SIMT编程通常需要大量Thread并行访问Global Memory。访存函数用于显式控制Global Memory访问时的缓存路径和缓存一致性维护方式，帮助开发者根据数据复用特征、写回方式和跨核可见性要求选择合适的加载、存储或Cache刷新接口。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/memory_access_functions/memory_access_functions_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 访存函数简介

SIMT 编程需要大量 Thread 并行访问 Global Memory。访存函数用于显式控制 Global Memory 访问时的缓存路径和缓存一致性维护方式。基本概念：Global Memory 为所有 Thread 可访问的全局内存；L2 Cache 可缓存读写数据；Data Cache 适合局部复用数据；Cache Line 为刷新基本粒度。

API 分类：加载函数 asc_ldcg（从 L2 Cache 加载，不写 Data Cache）、asc_ldca（优先 Data Cache，默认访存等价实现）；存储函数 asc_stcg（写 Global Memory 和 L2 Cache，不写 Data Cache）、asc_stwt（写 Global Memory、Data Cache 和 L2 Cache）；Cache 刷新函数 asc_dcci_single（刷新单条 Cache Line）、asc_dcci_entire（刷新整个 Data Cache，开销大慎用）；空操作函数 asc_nop（15 cycle 空操作）。

接口选择建议：数据有局部复用选 asc_ldca，仅依赖 L2 Cache 选 asc_ldcg；写入后可能被当前核再读选 asc_stwt，不希望污染 Data Cache 选 asc_stcg；跨核读取可能已被修改的数据用 DCCI 刷新。同一 Warp 内相邻 Thread 访问连续对齐地址可提升效率，可结合 float2/float4/int4 等向量类型减少指令数。DCCI 类接口处理 Cache 一致性，不等价于线程同步或原子操作。

<!-- cannbot:related:start -->
## 相关

- [DCacheAccess](../../../guides/operator_practice/simt_operator_optimization/memory_access/dcache_access.md)（`explains`）：DCache 策略依赖 asc_ldcg/asc_ldca/asc_stcg 等显式加载存储函数；接口导论解释缓存路径、写回与一致性，是实施优化的 API 依据。
- [MemoryAccessMerge](../../../guides/operator_practice/simt_operator_optimization/memory_access/memory_access_merge.md)（`explains`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《访存函数简介（内存访问函数）》提供“SIMT编程通常需要大量Thread并行访问Global Memory。访存函数用于显式控制Global Memory访问时的缓存路径和缓存一致性维护方式，帮助开发者根据数据复用特征、写回方式和跨核可见性要求选择合适的加载、存储或Cache刷新接口。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [AscLdca](asc_ldca.md)（`related`）：Ldca 展示带缓存策略的加载入口。
- [asc_dcci_single](asc_dcci_single.md)（`related`）：数据可见性维护是 load/store 之外的关键操作。
- [asc_ldcg（内存访问函数）](asc_ldcg.md)（`same_topic`）：asc_ldcg（内存访问函数） 与《访存函数简介（内存访问函数）》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [asc_stwt（内存访问函数）](asc_stwt.md)（`same_topic`）：asc_stwt（内存访问函数） 与《访存函数简介（内存访问函数）》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [访存函数](memory_access_functions.md)（`same_topic`）：总页列出 load/store/cache maintenance 接口及策略。
<!-- cannbot:related:end -->
