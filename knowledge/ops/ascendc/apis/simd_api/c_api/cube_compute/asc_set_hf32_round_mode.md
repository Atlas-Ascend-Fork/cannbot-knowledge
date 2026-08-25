---
type: API
title: AscSetHf32RoundMode
description: 设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_set_hf32_round_mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetHf32RoundMode

设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。

参数：hf32_round_mode(输入): HF32舍入模式控制入参，asc_hf32_round_mode枚举类型，支持如下2种枚举值： &nbsp;&nbsp;&bull; NEAREST_ZE。

约束：hf32_round_mode仅支持如下2种枚举值
- asc_hf32_round_mode::NEAREST_ZERO
- asc_hf32_round_mode::NEAREST_EVEN

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
