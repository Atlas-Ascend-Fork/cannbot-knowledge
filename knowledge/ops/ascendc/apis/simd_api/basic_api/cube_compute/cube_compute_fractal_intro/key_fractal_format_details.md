---
type: API
title: 关键分形格式详解
description: 矩阵分形存储格式是对多维Tensor在内存中数据排布格式的描述。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_fractal_intro/key_fractal_format_details.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# Cube Fractal格式关键说明

描述Cube计算中的关键Fractal数据排布格式，包括L0A/L0B的矩阵分块格式（Fractal）和L0C的结果分块格式。Fractal格式将大矩阵切分为固定大小的分块（如16x16），按特定顺序排布在Buffer中，以匹配Cube计算单元的硬件并行处理能力。

<!-- cannbot:related:start -->
## 相关

- [输出 z NZ 物理布局致 dim=1 间歇错位 banned](../../../../../runbooks/precision/z_nz_dim_1_banned.md)（`exemplifies`）：NZ dim=1 错位的根因在分形物理排布；关键分形格式详解给出 NZ 分块、轴映射和尾块解释，是重算地址与验证输出布局的依据。
- [卷积格式转换](../cube_store_key_features/convolution_format_conversion.md)（`related`）：焦点处理Cube 搬出阶段的 NZ/ND 格式转换；关键分形格式详解正文界定“矩阵分形存储格式是对多维Tensor在内存中数据排布格式的描述”。候选给出 ND2NZ 实现、Fixpipe 开关与 NZ 分形布局，能执行并验证焦点所述格式转换。
- [矩阵计算分形介绍](cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《关键分形格式详解》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [矩阵计算分形介绍](../../cube_compute_tensor_api/cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《关键分形格式详解》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [背景与核心概念](background_and_core_concepts.md)（`same_topic`）：关键分形页给出 A/B/C 主矩阵的 block 布局，是地址计算的直接依据。
<!-- cannbot:related:end -->
