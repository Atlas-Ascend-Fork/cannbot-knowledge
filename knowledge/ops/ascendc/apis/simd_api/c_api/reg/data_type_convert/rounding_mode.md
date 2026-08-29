---
type: API
title: 舍入模式与饱和模式
description: 在进行数据类型转换时，Ascend C API支持多种舍入模式和饱和模式。这些模式决定了当源数据类型转换为不同精度或范围的目标数据类型时，如何处理数值的舍入和溢出问题。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/rounding_mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 舍入模式与饱和模式

在进行数据类型转换时，Ascend C API支持多种舍入模式和饱和模式。这些模式决定了当源数据类型转换为不同精度或范围的目标数据类型时，如何处理数值的舍入和溢出问题。

在进行数据类型转换时，Ascend C API支持多种舍入模式和饱和模式。这些模式决定了当源数据类型转换为不同精度或范围的目标数据类型时，如何处理数值的舍入和溢出问题。

- 舍入模式：主要用于浮点数之间的转换或浮点数转整数时，确定如何将高精度数值舍入到低精度表示。
- 饱和模式/非饱和模式：处理数值超出目标数据类型表示范围时的溢出行为。
