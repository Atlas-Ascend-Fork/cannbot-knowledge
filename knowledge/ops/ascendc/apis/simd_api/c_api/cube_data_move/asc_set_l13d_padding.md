---
type: API
title: AscSetL13dPadding
description: 设置asc_copy_l12l0a搬运接口的Pad填充数值。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_l13d_padding.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetL13dPadding

设置Pad属性描述，用于在调用asc_copy_l12l0a接口时配置填充数值。

参数：config(输入): Pad填充值的数值。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL12L0a](asc_copy_l12l0a/asc_copy_l12l0a.md)（`related`）：《AscCopyL12L0a》明确“L1到L0A Buffer数据搬运接口集合，包含不同架构版本。”；它与《AscSetL13dPadding》的“设置asc_copy_l12l0a搬运接口的Pad填充数值。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscSetL12l0PaddingVal](../sys_var/asc_set_l12l0_padding_val.md)（`related`）：AscSetL13dPadding说明设置asc_copy_l12l0a搬运接口的Pad填充数值。
- [AscSetL13dFmatrix](asc_set_l13d_fmatrix.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscSetL13dPadding》具体提供“设置asc_copy_l12l0a搬运接口的Pad填充数值。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [asc_copy_l12l0a](asc_copy_l12l0a/asc_copy_l12l0a_arch_2201.md)（`related`）：《asc_copy_l12l0a》明确“用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里。包含2D格式搬运、3D格式搬运。”；它与《AscSetL13dPadding》的“设置asc_copy_l12l0a搬运接口的Pad填充数值。”在实际调用参数、数据流或结果校验上直接衔接。
- [asc_copy_l12l0a](asc_copy_l12l0a/asc_copy_l12l0a_arch_3510.md)（`related`）：《asc_copy_l12l0a》明确“用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里，包含2D格式搬运、2D格式转置搬运、3D格式搬运。”；它与《AscSetL13dPadding》的“设置asc_copy_l12l0a搬运接口的Pad填充数值。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscSetL13dRpt](asc_set_l13d_rpt.md)（`same_topic`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscSetL13dPadding》明确提供“设置asc_copy_l12l0a搬运接口的Pad填充数值。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
<!-- cannbot:related:end -->
