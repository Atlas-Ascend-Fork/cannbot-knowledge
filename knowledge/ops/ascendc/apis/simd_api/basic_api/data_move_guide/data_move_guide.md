---
type: API
title: 数据搬运导览
description: 数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/data_move_guide.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 数据搬运导览

AscendC 数据搬运接口的导航索引，按存储路径组织：GM↔UB、GM↔L1/L0、L1↔L0、L1/L0C↔UB、UB↔UB、L1↔Fixpipe Buffer、L1↔BiasTable Buffer。开发者可根据源与目的缓冲区位置选择对应搬运接口，搬运时需关注数据类型、对齐、block 拆分及 stride 约束，Cube 与矢量搬运的约束不同需分别对待。
