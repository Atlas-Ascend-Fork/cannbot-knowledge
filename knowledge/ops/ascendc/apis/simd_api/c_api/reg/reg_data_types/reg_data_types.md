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
