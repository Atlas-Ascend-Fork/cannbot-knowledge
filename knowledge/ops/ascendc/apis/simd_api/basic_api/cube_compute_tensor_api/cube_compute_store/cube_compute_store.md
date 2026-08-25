---
type: API
title: 矩阵计算的搬出
description: 矩阵计算 TensorAPI 搬出接口集，涵盖 L0C 到 GM、L0C 到 UB 的 Copy 接口及 L0C Buffer 内存结构。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_store/cube_compute_store.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 矩阵计算的搬出

矩阵计算 TensorAPI 搬出接口集，提供 L0C Buffer 计算结果向外部存储搬运的接口。
包含 L0C Buffer 内存结构介绍，以及 Copy 接口支持 L0C 到 Global Memory 和 L0C 到 Unified Buffer 两种搬运路径。
搬出过程可配合随路量化、随路 ReLU 等后处理特性，具体参见矩阵搬出关键特性说明。

<!-- cannbot:related:start -->
## 相关

- [Copy](copy_l0_c_to_ub.md)（`same_topic`）：《矩阵计算的搬出》明确“矩阵计算 TensorAPI 搬出接口集，涵盖 L0C 到 GM、L0C 到 UB 的 Copy 接口及 L0C Buffer 内存结构。”；它与《Copy》的“将L0C Buffer中的矩阵计算结果搬运到Unified Buffer，支持随路格式转换、量化输出、Relu和batch模式等特性。”在实际调用参数、数据流或结果校验上直接衔接。
- [CopyL1ToFixpipe](../cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：CopyL1ToFixpipe 与《矩阵计算的搬出》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算的搬出》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [矩阵计算的搬出](../../cube_compute/cube_compute_store/cube_compute_store.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《矩阵计算的搬出》明确“矩阵计算 TensorAPI 搬出接口集，涵盖 L0C 到 GM、L0C 到 UB 的 Copy 接口及 L0C Buffer 内存结构。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
<!-- cannbot:related:end -->
