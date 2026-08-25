---
type: API
title: AscSetL12l0PaddingVal
description: 设置PADDING_B寄存器值，存储搬运过程中的padding值。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_l12l0_padding_val.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetL12l0PaddingVal

对PADDING_B寄存器中的值进行设置，这是一个64bit的寄存器，用于存储搬运过程中padding的值。 其中各bit含义如下： 表1 PADDING_B寄存器比特位说明
函数原型：void asc_set_l12l0_padding_val(uint64_t config)
参数：config（输入）：待设置的寄存器值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSetL13dPadding](../cube_data_move/asc_set_l13d_padding.md)（`related`）：AscSetL13dPadding说明设置asc_copy_l12l0a搬运接口的Pad填充数值。
- [AscSetL13dRpt](../cube_data_move/asc_set_l13d_rpt.md)（`related`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscSetL12l0PaddingVal》明确提供“设置PADDING_B寄存器值，存储搬运过程中的padding值。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [SetLoadDataPaddingValue](../../basic_api/cube_compute/cube_load_aux_config/set_load_data_padding_value.md)（`related`）：SetLoadDataPaddingValue 与《AscSetL12l0PaddingVal》的实质衔接是：该配置在卷积 LoadData 前设定 padValue，Fmatrix/配置总览与 C API setter 是配置端；padding 参与数故障说明填充值不得进入有效 reduce count。
<!-- cannbot:related:end -->
