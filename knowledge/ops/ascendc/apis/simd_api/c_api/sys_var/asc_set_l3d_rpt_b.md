---
type: API
title: AscSetL3dRptB
description: 设置asc_copy_l12l0a/l0b的2D格式搬运repeat参数。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_l3d_rpt_b.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetL3dRptB

用于设置接口asc_copy_l12l0a、asc_copy_l12l0b的2D格式搬运的repeat参数。
函数原型：void asc_set_l3d_rpt_b(uint64_t config)
约束：需要配合接口asc_copy_l12l0a、asc_copy_l12l0b使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSetL13dFmatrix](../cube_data_move/asc_set_l13d_fmatrix.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscSetL3dRptB》具体提供“设置asc_copy_l12l0a/l0b的2D格式搬运repeat参数。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscSetL13dRpt](../cube_data_move/asc_set_l13d_rpt.md)（`related`）：“AscSetL3dRptB”定义：设置asc_copy_l12l0a/l0b的2D格式搬运repeat参数。；“AscSetL13dRpt”定义：设置Load3Dv2接口的repeat参数。。实质衔接：AscSetL3dRptB 配置 L1→L0A/L0B 2D repeat，SetL13dRpt 是相关 Load3D repeat 配置，真正消费者是 2201 的 asc_copy_l12l0a。
- [asc_copy_l12l0a](../cube_data_move/asc_copy_l12l0a/asc_copy_l12l0a_arch_2201.md)（`related`）：“AscSetL3dRptB”定义：设置asc_copy_l12l0a/l0b的2D格式搬运repeat参数。；“asc_copy_l12l0a”定义：用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里。包含2D格式搬运、3D格式搬运。。实质衔接：AscSetL3dRptB 配置 L1→L0A/L0B 2D repeat，SetL13dRpt 是相关 Load3D repeat 配置，真正消费者是 2201 的 asc_copy_l12l0a。
<!-- cannbot:related:end -->
