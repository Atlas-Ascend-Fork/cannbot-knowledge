---
type: API
title: 枚举类型
description: 枚举类型索引页，包含asc_hf32_round_mode、asc_load_l2_cache_mode与asc_store_l2_cache_mode。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/enum/enum_types.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 枚举类型（C API）

SIMD C API枚举类型集合，包含三个枚举定义。asc_hf32_round_mode用于Mmad计算开启HF32模式时FP32到HF32的舍入策略管理。asc_load_l2_cache_mode用于数据从GM搬运到UB时的L2 Cache管理策略，在asc_copy_gm2ub_align和asc_ndim_copy_gm2ub中作为参数。asc_store_l2_cache_mode用于数据从UB搬运到GM时的L2 Cache策略，在asc_copy_ub2gm_align中作为参数。合理配置Cache策略可显著提升数据搬运效率。
