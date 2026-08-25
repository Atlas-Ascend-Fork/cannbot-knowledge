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
