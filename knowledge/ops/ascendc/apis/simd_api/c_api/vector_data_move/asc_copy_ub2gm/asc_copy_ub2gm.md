---
type: API
title: AscCopyUb2Gm
description: UB到GM数据搬运接口集合，包含不同架构版本。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_ub2gm/asc_copy_ub2gm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscCopyUb2Gm

Unified Buffer到Global Memory数据搬运接口集合，用于将矢量计算结果从UB搬运回GM存储。按硬件架构版本区分不同实现：asc_copy_ub2gm_arch_2201适用于Atlas A2训练/推理系列和Atlas A3训练/推理系列产品，asc_copy_ub2gm_arch_3510适用于Ascend 950PR/Ascend 950DT。开发者应根据目标硬件选择对应架构版本的接口，不同架构版本在数据块大小和地址对齐约束上可能存在差异。

<!-- cannbot:related:start -->
## 相关

- [AscSetUb2gmLoopSize](../asc_set_ub2gm_loop_size.md)（`related`）：将数据从Unified Buffer (UB)搬运到Global Memory (GM)时，通过调用该接口设置内层循环和外层循环的次数。 以源操作数搬运场景为例，如下图所示。；Unified Buffer到Global Memory数据搬运接口集合，用于将矢量计算结果从UB搬运回GM存储。按硬件架构版本区分不同实现：asc_copy_ub2gm_arch_2201适用于Atlas A2训练/推理系列和Atlas A3训练/推理系列产品，asc_copy_ub2gm_arch_3510适用于Ascend 950PR/Ascend 950DT。开发者应根据目标硬件选择对应架构版本的接口，不同架构版本在数据块大小和地址对齐约束上可能存在差异。；循环设置接口为 UB→GM 搬运配置内外层迭代次数，asc_copy_ub2gm 是消费该方向配置并执行搬运的接口族。
<!-- cannbot:related:end -->
