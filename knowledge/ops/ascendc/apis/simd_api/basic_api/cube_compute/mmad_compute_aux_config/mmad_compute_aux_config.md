---
type: API
title: Mmad辅助配置说明
description: Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_aux_config/mmad_compute_aux_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Mmad辅助配置说明

Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。

控制Mmad/MmadWithSparse优先通过M/N的哪个方向。

本接口组包含 SetMMColumnMajor/SetMMRowMajor, SetHF32Mode, SetHF32TransMode。

本接口属于 Cube 矩阵计算接口。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
