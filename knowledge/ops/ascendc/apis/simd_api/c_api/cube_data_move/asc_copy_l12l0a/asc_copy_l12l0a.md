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

- [AscCopyGm2l0a](../asc_copy_gm2l0a.md)（`related`）：AscCopyL12L0A 提供先 GM→L1 再 L1→L0A 的分级加载替代路径，可据存储位置选择与直接 GM→L0A 的接口。
- [AscL13dFmatrixConfig](../../struct/asc_l13d_fmatrix_config.md)（`related`）：AscL13dFmatrixConfig 的 height、width 和四周 padding 参数由 AscCopyL12L0a 的 3D feature-map 搬运直接消费。
- [AscSetL13dFmatrix](../asc_set_l13d_fmatrix.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscCopyL12L0a》具体提供“L1到L0A Buffer数据搬运接口集合，包含不同架构版本。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscSetL13dPadding](../asc_set_l13d_padding.md)（`related`）：《AscCopyL12L0a》明确“L1到L0A Buffer数据搬运接口集合，包含不同架构版本。”；它与《AscSetL13dPadding》的“设置asc_copy_l12l0a搬运接口的Pad填充数值。”在实际调用参数、数据流或结果校验上直接衔接。
- [asc_copy_l12l0a](asc_copy_l12l0a_arch_2201.md)（`same_topic`）：总页定义 L1→L0A 搬运语义，2201 页给出该架构的签名与限制。
- [asc_copy_l12l0a](asc_copy_l12l0a_arch_3510.md)（`same_topic`）：asc_copy_l12l0a 与《AscCopyL12L0a》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
<!-- cannbot:related:end -->
