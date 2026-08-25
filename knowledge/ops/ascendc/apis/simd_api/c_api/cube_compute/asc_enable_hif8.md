---
type: API
title: AscEnableHif8
description: 用于设置Mmad计算开启HiF8模式，开启后L0A Buffer/L0B Buffer中的8bit数据将在参与矩阵乘法运算前被转化为hifloat8_t类型数据。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_enable_hif8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscEnableHif8

用于设置Mmad计算开启HiF8模式，开启该模式后L0A Buffer/L0B Buffer中的8bit数据将在参与矩阵乘法运算前被转化为hifloat8_t类型数据。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscEnableFp8](asc_enable_fp8.md)（`related`）：AscEnableFp8 与 AscEnableHif8 互斥选择 8bit Mmad 前的数据解释方式，直接提供 FP8 与 HiF8 模式选型。
- [Mmad](../../basic_api/cube_compute/mmad_compute/mmad.md)（`related`）：AscEnableHif8 只在随后 Mmad 消费 L0A/L0B 的 8bit 数据时生效，Mmad 是该模式配置的直接执行端。
<!-- cannbot:related:end -->
