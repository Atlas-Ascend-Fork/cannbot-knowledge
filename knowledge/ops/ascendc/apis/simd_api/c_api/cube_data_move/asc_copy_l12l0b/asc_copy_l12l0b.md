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

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2l0b](../asc_copy_gm2l0b.md)（`related`）：AscCopyL12L0b 是 GM 数据先进入 L1 后搬入 L0B 的第二段，与 AscCopyGm2l0b 的直达路径构成 B 矩阵搬入路线对照。
- [AscCopyL12L0bTrans](../asc_copy_l12l0b_trans/asc_copy_l12l0b_trans.md)（`related`）：普通 B 搬运不转置，按源布局选择。
- [AscL13dFmatrixConfig](../../struct/asc_l13d_fmatrix_config.md)（`related`）：同一 Fmatrix 配置也是 AscCopyL12L0b 3D 权重/特征搬运的几何输入，决定宽高与 padding 解释。
- [AscSetL13dFmatrix](../asc_set_l13d_fmatrix.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscCopyL12L0b》具体提供“L1到L0B Buffer数据搬运接口集合，包含不同架构版本。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscCopyL12l0bMx](../asc_copy_l12l0b_mx.md)（`same_topic`）：AscCopyL12l0bMx 与《AscCopyL12L0b》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [asc_copy_l12l0b](asc_copy_l12l0b_arch_3510.md)（`same_topic`）：总页定义 L1→L0B 搬运，3510 页给出架构签名。
<!-- cannbot:related:end -->
