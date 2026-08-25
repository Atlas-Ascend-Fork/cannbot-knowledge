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

- [SIMT协作组简介（高级编程）](../../../../guides/programming_guide/advanced_programming/simt_cooperative_groups.md)（`explains`）：焦点处理grid_group 与 thread_block 协作范围的选择；SIMT协作组简介（高级编程）正文说明“协作组（cooperative_groups）是Ascend C SIMT编程模型的扩展，用于组织协作线程组。协作组使开发者能够控制线程协作的粒度，实现更丰富、更高效的并行处理逻辑”。候选解释 grid 级和 block 级协作对象的不同同步/查询范围，避免选错作用域。
- [ThreadBlock](../thread_block/thread_block.md)（`related`）：焦点处理grid_group 与 thread_block 协作范围的选择；ThreadBlock正文说明“SIMT协作线程组thread_block接口集合，涵盖构造、同步、线程索引和维度查询等操作”。候选解释 grid 级和 block 级协作对象的不同同步/查询范围，避免选错作用域。
- [协作组](../cooperative_groups.md)（`related`）：GridGroup 是 cooperative_groups 的 Grid 级协作对象，覆盖跨 Thread Block 的组级操作。
- [协作组简介](../cooperative_groups_intro.md)（`related`）：焦点处理grid_group 与 thread_block 协作范围的选择；协作组简介正文说明“协作组（cooperative_groups）是Ascend C SIMT编程模型的一种拓展，用于组织协作线程组。通过协作组能够更细粒度地管理线程，从而实现更高效的线程并行协作”。候选解释 grid 级和 block 级协作对象的不同同步/查询范围，避免选错作用域。
- [BlockIndex](block_index.md)（`same_topic`）：焦点处理SIMT grid 中 block 索引及 grid_group 查询；GridGroup正文界定“SIMT协作线程组grid_group接口集合，涵盖构造、同步、线程和块索引查询等操作”。候选把线性 block 排名映射到 grid_group/GroupIndex，并用多核漏写案例验证索引分片。
<!-- cannbot:related:end -->
