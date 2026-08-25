---
type: API
title: 访存函数
description: 提供加载、存储、缓存控制等访存接口。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/memory_access_functions/memory_access_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 访存函数

提供 AICore SIMT 编程模型下的显式访存控制接口，包括全局内存加载（asc_ldcg、asc_ldca）、存储（asc_stcg、asc_stwt）、缓存无效化（asc_dcci_single、asc_dcci_entire）和空操作占位（asc_nop）。通过不同的加载存储策略和缓存提示，支持精细化的访存性能调优。

<!-- cannbot:related:start -->
## 相关

- [asc_ldcg（内存访问函数）](asc_ldcg.md)（`same_topic`）：asc_ldcg（内存访问函数） 与《访存函数》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [asc_stwt（内存访问函数）](asc_stwt.md)（`same_topic`）：asc_stwt（内存访问函数） 与《访存函数》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [访存函数简介（内存访问函数）](memory_access_functions_intro.md)（`same_topic`）：总页列出 load/store/cache maintenance 接口及策略。
<!-- cannbot:related:end -->
