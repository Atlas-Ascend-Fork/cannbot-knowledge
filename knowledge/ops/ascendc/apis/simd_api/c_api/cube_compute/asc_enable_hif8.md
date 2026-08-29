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

- [AscEnableFp8](asc_enable_fp8.md)（`related`）：用于设置Mmad计算开启FP8模式。该接口会关闭HiF8模式（与asc_enable_hif8相反），开启该模式后L0A Buffer/L0B Buffer中的FP8数据在参与Mmad计算之前不会被转化为hifloat8_t类型数据。；用于设置Mmad计算开启HiF8模式，开启该模式后L0A Buffer/L0B Buffer中的8bit数据将在参与矩阵乘法运算前被转化为hifloat8_t类型数据。两接口控制同一 Mmad 输入解释点的互斥模式，必须一起理解才能正确选择低精度路径。
<!-- cannbot:related:end -->
