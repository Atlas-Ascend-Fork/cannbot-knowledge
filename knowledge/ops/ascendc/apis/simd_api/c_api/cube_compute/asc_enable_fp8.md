---
type: API
title: AscEnableFp8
description: 用于设置Mmad计算开启FP8模式，关闭HiF8模式，使L0A/L0B Buffer中的FP8数据在参与Mmad计算前不转化为hifloat8_t类型。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_enable_fp8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscEnableFp8

用于设置Mmad计算开启FP8模式。该接口会关闭HiF8模式（与asc_enable_hif8相反），开启该模式后L0A Buffer/L0B Buffer中的FP8数据在参与Mmad计算之前不会被转化为hifloat8_t类型数据。

约束：- 与asc_enable_hif8相反，二者不同时生效。
- 需在asc_mmad执行前调用。

仅 Ascend 950PR/Ascend 950DT 支持。
