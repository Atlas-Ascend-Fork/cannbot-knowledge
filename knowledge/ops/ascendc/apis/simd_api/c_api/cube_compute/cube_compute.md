---
type: API
title: 矩阵计算
description: 矩阵计算接口索引页，汇总asc_mmad、asc_enable_hf32/fp8/hif8、asc_set_l0c2gm_config等Cube计算与配置接口。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/cube_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵计算

矩阵计算接口提供Cube核的矩阵乘与精度模式控制能力。核心接口asc_mmad执行矩阵乘法，asc_mmad_mx支持微缩放格式，asc_mmad_sparse支持稀疏矩阵乘。
精度模式接口asc_enable_hf32/hif8/fp8及asc_set_hf32_round_mode控制计算精度与舍入行为。asc_set_l0c2gm_config/nz2nd配置L0C到GM的搬运参数，asc_get_l0c2gm_prequant/relu/unitflag查询随路计算配置。asc_set_mmad_direction_m/n设置矩阵乘方向，asc_set_fp32_mode设置FP32计算模式。
