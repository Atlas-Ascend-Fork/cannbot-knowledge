---
type: API
title: 矩阵搬出寄存器配置说明
description: 本章节涉及寄存器在相同核函数内部会维持状态直到被人为改变，而在不同核函数内部不会继承之前的状态。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/cube_store_aux_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵搬出寄存器配置说明

矩阵计算 ISASI 搬出阶段的 Fixpipe 寄存器配置接口集。
涉及寄存器在相同核函数内部维持状态直到被人为改变，不同核函数之间不继承之前的状态。
包含 SetFixPipeConfig 设置总体配置，SetFixpipePreQuantFlag 控制随路量化开关，SetFixpipeNz2ndFlag 控制 NZ 到 ND 格式转换，SetFixPipeClipRelu 设置裁剪与 ReLU，SetFixPipeAddr 设置搬出地址。
