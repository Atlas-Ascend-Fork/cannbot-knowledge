---
type: API
title: AscCopyGm2Ub
description: GM到UB数据搬运接口集合，包含不同架构版本。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_gm2ub/asc_copy_gm2ub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscCopyGm2Ub

Global Memory到Unified Buffer数据搬运接口集合，用于将矢量计算的输入数据从GM搬运到UB。按硬件架构版本区分不同实现：asc_copy_gm2ub_arch_2201适用于Atlas A2训练/推理系列和Atlas A3训练/推理系列产品，asc_copy_gm2ub_arch_3510适用于Ascend 950PR/Ascend 950DT。开发者应根据目标硬件选择对应架构版本的接口，不同架构版本在数据块大小和地址对齐约束上可能存在差异。
