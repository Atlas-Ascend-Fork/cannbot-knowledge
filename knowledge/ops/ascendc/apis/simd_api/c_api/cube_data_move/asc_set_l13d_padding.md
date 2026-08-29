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
