---
type: API
title: 精度转换（数据结构）
description: 在了解不同类型之间的精度转换规则之前，需先了解二进制的精度舍入规则。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/precision_conversion.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 精度转换（数据结构）

不同数据类型间精度转换的舍入规则和溢出处理。源值超出目标类型表示范围时溢出，默认按饱和模式处理。主要转换路径：int4b_t→int16_t/half/bfloat16_t（无精度损失）；int8_t/uint8_t→half/float（无精度损失）；half→float（无精度损失）；float→half（CAST_RINT 舍入模式，尾数 23→10bits）；float→bfloat16_t（截断尾数 23→7bits）；float→int8_t/int4b_t（CAST_RINT 后饱和截断）；int32_t→half（反量化 DEQF16/REQ8 等，带量化参数）。

Cast 接口支持 RINT/CAST_RINT/CAST_NONE 等舍入模式。950 的 float32 尾数为 10bits，golden 数据生成需将量化参数低 13bits 清零。
