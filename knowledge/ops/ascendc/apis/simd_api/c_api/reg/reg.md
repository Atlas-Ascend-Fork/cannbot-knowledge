---
type: API
title: Reg矢量计算
description: C语言Reg矢量计算接口集合，涵盖数据类型、数据搬入搬出、算术计算、类型转换、同步控制等。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Reg矢量计算

C语言Reg矢量计算接口集合，提供基于矢量数据寄存器的计算能力。包含寄存器数据类型定义、数据搬入(reg_load)/搬出(reg_store)、基础算术、复合计算、逻辑计算、比较与选择、类型转换、归约计算、数据压缩、数据填充等子模块。
另含数据重排、直方图计算、索引操作、同步控制和系统变量访问等子模块，覆盖寄存器级矢量编程的完整能力。
