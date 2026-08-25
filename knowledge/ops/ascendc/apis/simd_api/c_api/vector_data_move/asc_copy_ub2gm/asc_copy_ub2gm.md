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

- [AscCopyGm2Ub](../asc_copy_gm2ub/asc_copy_gm2ub.md)（`related`）：反向 GM→UB 与本接口组成 copy-in/copy-out。
- [AscCopyUb2GmAlign](../asc_copy_ub2gm_align/asc_copy_ub2gm_align.md)（`related`）：Align 版本的地址/尾块契约不同，按物理对齐选择。
- [AscCopyUb2l1](../asc_copy_ub2l1.md)（`related`）：UB→GM 写回与 UB→L1 服务不同下游存储层。
- [AscSetUb2gmLoop1Stride](../asc_set_ub2gm_loop1_stride.md)（`related`）：AscCopyUb2Gm is the transfer operation that consumes the loop1 stride configured by the focal setter.
- [AscCopyUb2GmAlign](../asc_copy_ub2gm_align/asc_copy_ub2gm_align_arch_2201.md)（`same_topic`）：AscCopyUb2GmAlign 与《AscCopyUb2Gm》的实质衔接是：UB→GM aligned 搬运与普通/2201 变体、反向 GM→UB、pad 和 loop 配置组成同一非对齐数据通路。
- [asc_copy_ub2gm](asc_copy_ub2gm_arch_2201.md)（`same_topic`）：asc_copy_ub2gm 与《AscCopyUb2Gm》的实质衔接是：UB→GM 基础搬运与 aligned 变体、反向 GM→UB 组成数据通路；loop stride/size 与 pad 值必须在调用前按 2201 契约配置。
- [asc_copy_ub2gm](asc_copy_ub2gm_arch_3510.md)（`same_topic`）：3510 变体给出 Ascend950 的签名和能力。
<!-- cannbot:related:end -->
