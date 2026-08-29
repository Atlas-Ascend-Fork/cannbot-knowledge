---
type: API
title: AscCopyL12L0a
description: L1到L0A Buffer数据搬运接口集合，包含不同架构版本。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0a/asc_copy_l12l0a.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscCopyL12L0A

L1 Buffer到L0A Buffer数据搬运接口集合，用于将矩阵计算的左矩阵数据从L1搬运到L0A。按硬件架构版本区分不同实现：asc_copy_l12l0a_arch_2201适用于Atlas A2训练/推理系列和Atlas A3训练/推理系列产品，asc_copy_l12l0a_arch_3510适用于Ascend 950PR/Ascend 950DT。开发者应根据目标硬件选择对应架构版本的接口，不同架构版本在数据块大小、地址对齐和stride参数约束上可能存在差异。

<!-- cannbot:related:start -->
## 相关

- [AscSetL13dFmatrix](../asc_set_l13d_fmatrix.md)（`related`）：设置Feature map属性描述，用于在调用asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口时配置填充数值。；L1 Buffer到L0A Buffer数据搬运接口集合，用于将矩阵计算的左矩阵数据从L1搬运到L0A。按硬件架构版本区分不同实现：asc_copy_l12l0a_arch_2201适用于Atlas A2训练/推理系列和Atlas A3训练/推理系列产品，asc_copy_l12l0a_arch_3510适用于Ascend 950PR/Ascend 950DT。开发者应根据目标硬件选择对应架构版本的接口，不同架构版本在数据块大小、地址对齐和stride参数约束上可能存在差异。；AscSetL13DFmatrix 为 asc_copy_l12l0a 的 3D 搬运配置 Feature map 与填充值，AscCopyL12L0A 是消费该配置完成 L1 到 L0A 左矩阵搬运的接口集合。
- [asc_copy_l12l0a](asc_copy_l12l0a_arch_2201.md)（`same_topic`）：“asc_copy_l12l0a_arch_2201适用于Atlas A2训练/推理系列和Atlas A3训练/推理系列产品”与“本接口不支持2D格式搬运的转置场景”把总览的平台选择落到 2201 版本的能力边界。
- [asc_copy_l12l0a](asc_copy_l12l0a_arch_3510.md)（`same_topic`）：“asc_copy_l12l0a_arch_3510适用于Ascend 950PR/Ascend 950DT”与“包含2D格式搬运、2D格式转置搬运、3D格式搬运”把总览的平台选择落到 3510 版本扩展的转置能力。
<!-- cannbot:related:end -->
