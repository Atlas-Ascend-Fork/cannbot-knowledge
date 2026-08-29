---
type: API
title: AscCopyL12Fb
description: L1到Fb Buffer数据搬运接口集合，包含不同架构版本。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12fb/asc_copy_l12fb.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscCopyL12Fb

L1 Buffer到Fb Buffer数据搬运接口集合，用于矩阵计算场景中将中间结果或量化参数从L1搬运到Fixpipe Buffer。按硬件架构版本区分不同实现：asc_copy_l12fb_arch_2201适用于Atlas A2训练/推理系列和Atlas A3训练/推理系列产品，asc_copy_l12fb_arch_3510适用于Ascend 950PR/Ascend 950DT。开发者应根据目标硬件选择对应架构版本的接口，不同架构版本在参数约束和地址对齐要求上可能存在差异。
