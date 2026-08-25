---
type: API
title: reg数据类型定义
description: 定义矢量数据寄存器的数据类型，按位宽分类列举vector_int8_t、vector_half、vector_float等类型，仅Ascend 950PR/950DT支持。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_data_types/data_type_definition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# reg数据类型定义

定义矢量数据寄存器的数据类型，按位宽分类列举vector_int8_t、vector_half、vector_float等类型，仅Ascend 950PR/950DT支持。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscCreateMask](asc_create_mask.md)（`same_topic`）：AscCreateMask 与《reg数据类型定义》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [寄存器数据类型](reg_data_types.md)（`same_topic`）：寄存器数据类型 的核心契约是“寄存器数据类型相关接口汇总，包含数据类型定义、地址寄存器更新、掩码创建与获取等能力”；reg数据类型定义 补充“定义矢量数据寄存器的数据类型，按位宽分类列举vector_int8_t、vector_half、vector_float等类型，仅Ascend 950PR/950DT支持”。
<!-- cannbot:related:end -->
