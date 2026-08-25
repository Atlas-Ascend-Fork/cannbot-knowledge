---
type: API
title: Memory矢量计算
description: Memory矢量计算类接口汇总，覆盖算术、逻辑、比较、归约、类型转换、数据搬运等基于内存操作的矢量计算能力。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/memory_vector_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Memory矢量计算

Memory矢量计算接口提供基于UB内存的矢量运算能力。算术运算含asc_add/sub/mul/div/exp/log/sqrt/rcp/rsqrt及asc_add_relu/sub_relu/mul_add/mul_add_relu等融合激活变体。
比较运算含asc_eq/ge/gt/le/lt/ne及_scalar变体，归约含asc_reduce/datablock_reduce_max/min/sum及asc_repeat_reduce和asc_pair_reduce_sum。类型转换覆盖bfloat16/half/float/int系列互转。
另含asc_copy/duplicate/gather/brcb/transpose/bitsort/mrgsort4等数据操作，asc_set_vector_mask/mask_count/mask_norm控制矢量掩码，asc_set_deq_scale设置反量化系数。asc_squeeze支持数据解压。
