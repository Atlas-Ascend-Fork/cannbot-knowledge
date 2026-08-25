---
type: API
title: SetHF32TransMode
description: 设置HF32模式取整的具体方式，需要先使用SetHF32Mode开启HF32取整模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_aux_config/SetHF32TransMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetHF32TransMode

设置 HF32 模式下 FP32 到 HF32 的取整方式。须先调用 SetHF32Mode 开启 HF32 模式。

参数：mode 为 HF32TransMode 枚举，NEAREST_ZERO 向零靠近四舍五入、NEAREST_EVEN 最接近偶数四舍五入。支持 950/a2/a3/Atlas 200I/500 A2，不支持 Atlas 推理/训练系列。
