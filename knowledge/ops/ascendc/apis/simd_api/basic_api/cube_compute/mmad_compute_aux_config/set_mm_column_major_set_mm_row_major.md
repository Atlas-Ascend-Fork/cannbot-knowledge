---
type: API
title: SetMMColumnMajor/SetMMRowMajor
description: 控制Mmad/MmadWithSparse优先通过M/N的哪个方向。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_aux_config/SetMMColumnMajor-SetMMRowMajor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetMMColumnMajor/SetMMRowMajor

控制 Mmad/MmadWithSparse 的计算方向优先级。SetMMColumnMajor 表示 Cube 先沿 M 方向再沿 N 方向生成结果；SetMMRowMajor 表示先沿 N 方向再沿 M 方向。开启 unitFlag 时需配合设置：Fixpipe 开启 NZ2ND/ChannelMerge 时用 SetMMRowMajor，否则用 SetMMColumnMajor。支持 950/a2/a3/Atlas 200I/500 A2。
