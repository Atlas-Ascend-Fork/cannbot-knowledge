---
type: API
title: 矩阵搬出关键特性说明
description: 矩阵搬出关键特性说明，包含随路量化、随路 Relu、F32 Channel Split、Int8 Channel Merge、batch 搬运等。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_store_key_features/cube_store_key_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵搬出关键特性说明

矩阵计算 TensorAPI 搬出阶段支持的关键后处理特性，在 L0C 到 GM/UB 搬运过程中随路完成。
包含随路量化（Quant）与随路 ReLU 激活，支持在搬出时同时完成精度转换与激活计算，减少额外计算开销。
F32 Channel Split 和 Int8 Channel Merge 分别支持浮点通道拆分与整型通道合并，batch 搬运支持多 batch 数据的一次性搬出。
L0C Buffer 到 Unified Buffer 双目标模式支持同时向 UB 搬运数据，适配特定计算场景。

<!-- cannbot:related:start -->
## 相关

- [F32 Channel Split](../../cube_compute/cube_store_key_features/f32_channel_split.md)（`related`）：矩阵搬出关键特性说明说明矩阵搬出关键特性说明，包含随路量化、随路 Relu、F32 Channel Split、Int8 Channel Merge、batch 搬运等；对F32 Channel Split而言，Channel Split 是 L0C 搬出关键特性，只有总览补齐其与格式转换、量化、ReLU 组合时的选型约束。
- [矩阵搬出关键特性说明](../../cube_compute/cube_store_key_features/cube_store_key_features.md)（`related`）：TensorAPI 的矩阵搬出特性与 ISASI 卡覆盖相同的 NZ 转换、通道拆并和随路量化/ReLU，但面向不同编程接口。
- [随路ReLU](../../cube_compute/cube_store_key_features/accompanying_relu.md)（`related`）：Tensor API 搬出特性页说明 ReLU 与量化可在 L0C 到 GM/UB 搬运时一起完成，解释 enableRelu 版本能力的执行位置。
- [随路Relu](relu_pre.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《矩阵搬出关键特性说明》具体提供“矩阵搬出关键特性说明，包含随路量化、随路 Relu、F32 Channel Split、Int8 Channel Merge、batch 搬运等。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [CopyL1ToFixpipe](../cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：CopyL1ToFixpipe 与《矩阵搬出关键特性说明》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵搬出关键特性说明》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
<!-- cannbot:related:end -->
