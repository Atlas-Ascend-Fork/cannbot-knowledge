---
type: API
title: AscSetL13dFmatrix
description: 设置3D搬运接口的Feature map属性描述，用于配置填充数值。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_l13d_fmatrix.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetL13dFmatrix

设置Feature map属性描述，用于在调用asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口时配置填充数值。
仅当asc_copy_l12l0a/asc_copy_l12l0b接口的f_matrix_ctrl参数指示从左矩阵获取FeatureMap的属性时使用本接口设置Feature map属性描述，否则使用asc_set_l13d_fmatrix_b接口。

参数：config(输入): 用于设置asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口的Feature map属性参数，详细说明请参考asc_l13d_。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL12L0a](asc_copy_l12l0a/asc_copy_l12l0a.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscCopyL12L0a》具体提供“L1到L0A Buffer数据搬运接口集合，包含不同架构版本。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscCopyL12L0b](asc_copy_l12l0b/asc_copy_l12l0b.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscCopyL12L0b》具体提供“L1到L0B Buffer数据搬运接口集合，包含不同架构版本。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscCopyL12L0bTrans](asc_copy_l12l0b_trans/asc_copy_l12l0b_trans.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscCopyL12L0bTrans》具体提供“将数据从L1 Buffer搬运到L0B Buffer并支持转置的接口，包含不同架构版本的具体实现。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscL13dFmatrixConfig](../struct/asc_l13d_fmatrix_config.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscL13dFmatrixConfig》具体提供“用于设置3D格式搬运接口的Feature map属性参数，包括宽高和四周填充大小。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscSetL13dFmatrixB](asc_set_l13d_fmatrix_b.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscSetL13dFmatrixB》具体提供“设置3D搬运接口右矩阵的Feature map属性描述，用于配置填充数值。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscSetL13dPadding](asc_set_l13d_padding.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscSetL13dPadding》具体提供“设置asc_copy_l12l0a搬运接口的Pad填充数值。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscSetL13dSize](asc_set_l13d_size.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscSetL13dSize》具体提供“设置3D搬运接口在L1 Buffer的边界值。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscSetL3dRptB](../sys_var/asc_set_l3d_rpt_b.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscSetL3dRptB》具体提供“设置asc_copy_l12l0a/l0b的2D格式搬运repeat参数。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [SetFmatrix](../../basic_api/cube_compute/cube_load_aux_config/set_fmatrix.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《SetFmatrix》具体提供“调用LoadData（卷积数据搬运）时设置FeatureMap的属性描述，包括l1H、l1W、padList和fmatrixMode，需在LoadData接口前调用。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscCopyL12l0bMx](asc_copy_l12l0b_mx.md)（`same_topic`）：AscCopyL12l0bMx 与《AscSetL13dFmatrix》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscSetL13dRpt](asc_set_l13d_rpt.md)（`same_topic`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscSetL13dFmatrix》明确提供“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [SetFmatrixBitMode](../../basic_api/cube_compute/cube_load_aux_config/set_fmatrix_bit_mode.md)（`same_topic`）：SetFmatrixBitMode 与《AscSetL13dFmatrix》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
<!-- cannbot:related:end -->
