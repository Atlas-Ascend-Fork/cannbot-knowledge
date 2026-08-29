---
type: API
title: 矩阵计算（ISASI）
description: AscendC 矩阵计算 ISASI 接口总览，涵盖搬入、Mmad 计算、搬出及辅助配置与关键特性说明。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 矩阵计算（ISASI）

Ascend C 矩阵计算 ISASI 接口导航页，提供基于底层指令的矩阵计算完整流程接口。
涵盖矩阵计算分形介绍、搬入（LoadData/DataCopy 等）、搬入辅助配置、Mmad 计算、Mmad 关键特性与辅助配置、搬出（DataCopy/Fixpipe）、搬出关键特性与寄存器配置。
相较于 TensorAPI，ISASI 接口更接近硬件指令层级，提供更细粒度的控制能力但编程复杂度更高。
