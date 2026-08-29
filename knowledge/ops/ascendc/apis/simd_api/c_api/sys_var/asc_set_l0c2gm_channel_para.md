---
type: API
title: AscSetL0c2gmChannelPara
description: 设置通道步长寄存器比特位，配合L0C搬运接口使用。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_l0c2gm_channel_para.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetL0c2gmChannelPara

对通道步长参数的专用寄存器的比特位进行设置。需要配合接口asc_copy_l0c2l1或asc_copy_l0c2gm使用。 仅当调用接口时开启NZ2DN模式时，此功能才有效。
函数原型：void asc_set_l0c2gm_channel_para(uint64_t config)
约束：需要在对应的数据搬运接口之前调用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscCopyL0c2Gm](../cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm_arch_3510.md)（`related`）：“对通道步长参数的专用寄存器的比特位进行设置。需要配合接口asc_copy_l0c2l1或asc_copy_l0c2gm使用。 仅当调用接口时开启NZ2DN模式时，此功能才有效。”与“该接口用于将矩阵计算的结果从L0C Buffer搬运至Global Memory（GM）中，并且在搬运过程中支持与其它接口组合使用，配置多种随路能力。”提供双方正文证据。setter 正文直接指定 asc_copy_l0c2gm 且只在 NZ2DN 模式生效，搬运卡定义 L0C 到 GM 及组合随路能力，形成配置先于搬运的调用关系。
<!-- cannbot:related:end -->
