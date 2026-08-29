---
type: API
title: GridGroup
description: SIMT协作线程组grid_group接口集合，涵盖构造、同步、线程和块索引查询等操作。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/grid_group.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GridGroup

grid_group对核函数启动的所有SIMT线程进行抽象，线程范围覆盖当前Grid中所有线程块及其线程。提供is_valid有效性查询和sync跨线程块同步。
静态查询接口含thread_rank（全局线程排名）、block_rank（线程块排名）、num_threads/size（总线程数）、num_blocks（总线程块数）、dim_blocks/group_dim/block_index（维度与索引信息）。
仅支持SIMT编程场景，不支持SIMD与SIMT混合编程。

<!-- cannbot:related:start -->
## 相关

- [GridGroupConstructor](grid_group_constructor.md)（`related`）：grid_group对核函数启动的所有SIMT线程进行抽象，线程范围覆盖当前Grid中所有线程块及其线程。提供is_valid有效性查询和sync跨线程块同步。；grid_group不提供默认的构造函数，用户使用this_grid函数获取当前Grid对应的grid_group对象。。对象卡说明 grid_group 能力范围，构造卡给出取得该对象并使用这些能力的唯一入口。
<!-- cannbot:related:end -->
