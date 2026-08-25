---
type: API
title: Tiling数据结构注册
description: Tiling数据结构注册接口索引。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_data_structure_register/Tiling_data_structure_register.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Tiling数据结构注册

提供 TilingData 结构体的定义与注册能力。TilingData 结构定义通过 BEGIN_TILING_DATA_DEF、TILING_DATA_FIELD_DEF、TILING_DATA_FIELD_DEF_ARR、TILING_DATA_FIELD_DEF_STRUCT 和 END_TILING_DATA_DEF 等宏定义字段，继承 TilingDef 后自动生成 set_/get_ 接口用于 Host 侧读写字段值。
TilingData 结构注册通过 REGISTER_TILING_DATA_CLASS 宏将 TilingData 类与算子绑定，支持注册默认结构体、中间结构体（虚拟算子名为 struct_name#Op）和按 tiling_key 定制的结构体（op_type 命名为 ${op_type}_${tiling_key}）。
约束：字段仅支持 int8_t~uint64_t、float 等通用数据类型；结构体成员需满足字节对齐；tiling 结构体名需全局唯一，不同算子注册同名不同结构体会产生未定义行为。需包含头文件 register/tilingdata_base.h。
