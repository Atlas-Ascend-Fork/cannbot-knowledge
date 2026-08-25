---
type: API
title: AscCopyL12L0b
description: L1到L0B Buffer数据搬运接口集合，包含不同架构版本。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0b/asc_copy_l12l0b.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscCopyL12L0B

L1 Buffer到L0B Buffer数据搬运接口集合，用于将矩阵计算的右矩阵数据从L1搬运到L0B。按硬件架构版本区分不同实现：asc_copy_l12l0b_arch_2201适用于Atlas A2训练/推理系列和Atlas A3训练/推理系列产品，asc_copy_l12l0b_arch_3510适用于Ascend 950PR/Ascend 950DT。开发者应根据目标硬件选择对应架构版本的接口，不同架构版本在数据块大小、地址对齐和stride参数约束上可能存在差异。
