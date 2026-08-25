---
type: API
title: 辅助矩阵分形格式详解
description: 针对Ascend 950PR/Ascend 950DT产品：
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_fractal_intro/aux_cube_fractal_format_details.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# Cube Fractal格式详细说明（辅助）

详细描述Cube计算中各存储层次的数据Fractal排布格式，包括L1 Buffer的NZ/ZN格式、L0A/L0B的Fractal格式、L0C的Fractal格式等。涵盖各格式在不同数据类型（half/float/int8等）下的具体排布参数（C0、N0、M0等）和地址计算方法。

<!-- cannbot:related:start -->
## 相关

- [卷积格式转换](../cube_store_key_features/convolution_format_conversion.md)（`related`）：焦点处理Cube 搬出阶段的 NZ/ND 格式转换；辅助矩阵分形格式详解正文界定“针对Ascend 950PR/Ascend 950DT产品：”。候选给出 ND2NZ 实现、Fixpipe 开关与 NZ 分形布局，能执行并验证焦点所述格式转换。
- [矩阵计算分形介绍](cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《辅助矩阵分形格式详解》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [矩阵计算分形介绍](../../cube_compute_tensor_api/cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《辅助矩阵分形格式详解》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [背景与核心概念](background_and_core_concepts.md)（`same_topic`）：辅助分形页补充 bias/scale 等 buffer 格式，连接概念与辅助数据搬运。
<!-- cannbot:related:end -->
