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

- [AscCopyL12L0a](asc_copy_l12l0a/asc_copy_l12l0a.md)（`related`）：设置Feature map属性描述，用于在调用asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口时配置填充数值。；L1 Buffer到L0A Buffer数据搬运接口集合，用于将矩阵计算的左矩阵数据从L1搬运到L0A。按硬件架构版本区分不同实现：asc_copy_l12l0a_arch_2201适用于Atlas A2训练/推理系列和Atlas A3训练/推理系列产品，asc_copy_l12l0a_arch_3510适用于Ascend 950PR/Ascend 950DT。开发者应根据目标硬件选择对应架构版本的接口，不同架构版本在数据块大小、地址对齐和stride参数约束上可能存在差异。；AscSetL13DFmatrix 为 asc_copy_l12l0a 的 3D 搬运配置 Feature map 与填充值，AscCopyL12L0A 是消费该配置完成 L1 到 L0A 左矩阵搬运的接口集合。
- [AscL13dFmatrixConfig](../struct/asc_l13d_fmatrix_config.md)（`related`）：asc_l13d_fmatrix_config用于设置asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口的Feature map属性参数；设置Feature map属性描述，用于在调用asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口时配置填充数值。结构体卡定义 Feature map 配置载体，设置接口把该描述写入 3D 搬运状态；联合阅读可确定 asc_copy_l12l0a/b 前的参数构造与设置顺序。
<!-- cannbot:related:end -->
