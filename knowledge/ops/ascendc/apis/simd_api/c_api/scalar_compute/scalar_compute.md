---
type: API
title: 标量计算
description: 标量计算类接口汇总，提供位操作、前导零计数、数据加载存储及标量原子操作等能力。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/scalar_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 标量计算

C API标量计算接口提供位操作、数据加载存储和标量原子操作。位操作含asc_popc（位计数）、asc_clz（前导零）、asc_ffs/ffz（位查找）、asc_set_nthbit/clear_nthbit（位设置/清除）、asc_sflbits（位翻转）、asc_zero_bits_cnt。
数据访问含asc_load_dev/store_dev设备端加载存储，asc_float2int32标量类型转换。
原子操作含asc_atomic_add/sub/exch/max/min/inc/dec/cas/and/or/xor，保证单次读-改-写原子性。
