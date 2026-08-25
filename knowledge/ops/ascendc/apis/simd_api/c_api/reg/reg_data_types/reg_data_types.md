---
type: API
title: 寄存器数据类型
description: 寄存器数据类型相关接口汇总，包含数据类型定义、地址寄存器更新、掩码创建与获取等能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_data_types/reg_data_types.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 寄存器数据类型

寄存器数据类型相关接口提供矢量数据寄存器的类型定义和辅助操作。含reg数据类型定义、asc_update_addr_reg地址寄存器更新。
掩码操作含asc_create_mask创建掩码、asc_update_mask更新掩码、asc_get_mask_spr从特殊寄存器获取掩码。asc_create_iter_reg已废弃。

<!-- cannbot:related:start -->
## 相关

- [AscCreateMask](asc_create_mask.md)（`same_topic`）：AscCreateMask 与《寄存器数据类型》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [asc_create_iter_reg (废弃)](asc_create_iter_reg_deprecated.md)（`same_topic`）：类型总页给出 IterReg 的废弃状态和当前寄存器类型。
- [reg数据类型定义](data_type_definition.md)（`same_topic`）：寄存器数据类型 的核心契约是“寄存器数据类型相关接口汇总，包含数据类型定义、地址寄存器更新、掩码创建与获取等能力”；reg数据类型定义 补充“定义矢量数据寄存器的数据类型，按位宽分类列举vector_int8_t、vector_half、vector_float等类型，仅Ascend 950PR/950DT支持”。
<!-- cannbot:related:end -->
