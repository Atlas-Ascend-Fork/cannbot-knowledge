---
type: API
title: 类型转换辅助配置接口
description: 类型转换辅助配置接口索引页，包含SetDeqScale。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/type_conversion_aux_config/type_conversion_aux_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 类型转换辅助配置接口

提供 SetDeqScale 接口，用于设置 DEQSCALE 寄存器（64bit）的值，供 Vector 计算单元量化计算使用。寄存器中存放的参数在不同场景下含义不同：s322fp16 场景下 bits 0-15 为 half 类型 scale；s162b8 不开启向量量化场景下 bits 0-31 为 float scale、bits 37-45 为 offset、bit 46 为 signMode；s162b8 开启向量量化场景下 bits 0-13 为指向 UB 的 vdeqAddr。
