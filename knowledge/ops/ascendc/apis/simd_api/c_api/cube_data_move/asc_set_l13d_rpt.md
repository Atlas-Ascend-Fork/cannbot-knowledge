---
type: API
title: AscSetL13dRpt
description: 设置Load3Dv2接口的repeat参数。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_l13d_rpt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetL13dRpt

用于设置Load3Dv2接口的repeat参数。

参数：config(输入): 用于设置Load3Dv2接口的repeat参数，详细说明请参考asc_load3d_v2_config.md。

约束：- 需配合asc_load3d_v2_config.md使用，用于设置Load3Dv2接口的repeat参数。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2l0a](asc_copy_gm2l0a.md)（`related`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscCopyGm2l0a》明确提供“将数据从GM搬运到L0A Buffer。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [AscCopyGm2l0b](asc_copy_gm2l0b.md)（`related`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscCopyGm2l0b》明确提供“将矩阵数据从GM搬运到L0B Buffer。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [AscCopyL12L0bTrans](asc_copy_l12l0b_trans/asc_copy_l12l0b_trans_arch_2201.md)（`related`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscCopyL12L0bTrans》明确提供“实现带转置的2D格式数据从L1 Buffer到L0B Buffer的加载，支持多种数据类型和分形处理。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [AscCopyL12l0aTrans](asc_copy_l12l0a_trans.md)（`related`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscCopyL12l0aTrans》明确提供“将2D格式数据带转置地从L1 Buffer加载到L0A Buffer。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [AscCopyL12l0bSparse](asc_copy_l12l0b_sparse.md)（`related`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscCopyL12l0bSparse》明确提供“将L1 Buffer中的稠密权重矩阵搬运到L0B Buffer，同时读取索引矩阵用于稠密矩阵稀疏化。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [AscLoad3dV2Config](../struct/asc_load3d_v2_config.md)（`related`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscLoad3dV2Config》明确提供“用于设置Load3Dv2接口的repeat参数，包括迭代步长、次数和方向。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [AscSetL12l0PaddingVal](../sys_var/asc_set_l12l0_padding_val.md)（`related`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscSetL12l0PaddingVal》明确提供“设置PADDING_B寄存器值，存储搬运过程中的padding值。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [AscSetL3dRptB](../sys_var/asc_set_l3d_rpt_b.md)（`related`）：“AscSetL3dRptB”定义：设置asc_copy_l12l0a/l0b的2D格式搬运repeat参数。；“AscSetL13dRpt”定义：设置Load3Dv2接口的repeat参数。。实质衔接：AscSetL3dRptB 配置 L1→L0A/L0B 2D repeat，SetL13dRpt 是相关 Load3D repeat 配置，真正消费者是 2201 的 asc_copy_l12l0a。
- [AscSetL13dFmatrix](asc_set_l13d_fmatrix.md)（`same_topic`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscSetL13dFmatrix》明确提供“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [AscSetL13dFmatrixB](asc_set_l13d_fmatrix_b.md)（`same_topic`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscSetL13dFmatrixB》明确提供“设置3D搬运接口右矩阵的Feature map属性描述，用于配置填充数值。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [AscSetL13dPadding](asc_set_l13d_padding.md)（`same_topic`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscSetL13dPadding》明确提供“设置asc_copy_l12l0a搬运接口的Pad填充数值。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [AscSetL13dSize](asc_set_l13d_size.md)（`same_topic`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscSetL13dSize》明确提供“设置3D搬运接口在L1 Buffer的边界值。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
<!-- cannbot:related:end -->
