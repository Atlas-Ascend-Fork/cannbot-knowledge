---
type: Guide
title: MxMatmul场景
description: 带有量化系数的矩阵乘法，左右矩阵分别配有scaleA和scaleB量化系数矩阵，支持MXFP8、MXFP4等低位宽数据类型。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/mx_matmul_scenario.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# MxMatmul场景

## 背景介绍
浮点数在科学计算、图像处理、神经网络等领域应用广泛。以AI训练为例，现有的浮点数格式或数值范围不足，或精度不高，这影响了模型的收敛速度和性能。如果要同时满足数值范围和精度的要求，将会导致内存占用过大，从而增加数据存储和传输的成本。基于此种情况，业内提出了一种新的浮点数格式——微缩放（Microscaling，MX）格式。MX格式的浮点数可以支持更低比特位宽的AI训练和推理，并且占用的内存更少。符合MX标准的数据格式在使用8位或更低比特位的情况下，能够实现稳健的AI训练和推理模型精度。
MX格式是一种块数据格式，若干个数据可以组成一个块（或者一个组），数据以块为单位。MX格式的数据由三部分构成：
-   共享缩放因子X，位宽为w bits；
-   私有元素Pi，位宽为d bits；
-   块大小k，表示多少个低比特数据形成一个块；
所有k个元素Pi有相同的位宽和数据类型，并且共享一个缩放因子X，每个包含k个元素的块可以使用（w+k*d）位进行编码。元素的数据类型和缩放因子可以独立选择。
下图为MX格式的浮点数的数据结构，S、E和M分别用于表示浮点数的符号、指数和尾数字段的值。其中，共享缩放因子X是一个用于整个数据块的缩放比例因子，它决定了数据块中所有元素的动态范围。通过引入共享缩放因子，MX格式的数据能够在保持低位宽的同时，灵活地表示不同范围的数据。块大小k指的是组成一个数据块（或组）的低比特数据的数量。私有元素Pi是指数据块中的每个低比特数据元素。这些元素经过缩放因子X的调整后，共同表示了一个高精度的浮点数或整数。
MX格式的数据类型包含多种，例如MXFP8、MXFP4、MXFP16、MXINT4等。下表列举了MxMatmul场景（全称Microscaling Matmul）支持的数据类型。
MxMatmul支持MX格式的数据类型
MXFP8：fp8_e5m2_t：8：32：fp8_e8m0_t：8
MXFP8：fp8_e4m3fn_t：8：32：fp8_e8m0_t：8
MXFP4：fp4x2_e1m2_t：4：32：fp8_e8m0_t：8
MXFP4：fp4x2_e2m1_t：4：32：fp8_e8m0_t：8
## 功能介绍
MxMatmul（全称Microscaling Matmul）为带有量化系数的矩阵乘法，即左矩阵和右矩阵均有对应的量化系数矩阵，左量化系数矩阵scaleA和右量化系数矩阵scaleB。MxMatmul场景中，左量化系数矩阵与左矩阵乘积，右量化系数矩阵与右矩阵乘积，对两个乘积的结果做矩阵乘法。
MxMatmul的计算公式为：C = (scaleA ⊗ A) * (scaleB ⊗ B) + Bias，“⊗”表示广播乘法，左/右矩阵与左/右量化系数矩阵做乘积时，K方向上每32个元素共享一个量化因子，如图2所示。

<!-- cannbot:related:start -->
## 相关

- [SetMadType](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_mad_type.md)（`explains`）：MxMatmul（全称Microscaling Matmul）为带有量化系数的矩阵乘法；在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景。场景卡定义带 scaleA/scaleB 的 MxMatmul 语义，SetMadType 卡给出该场景生成正确 Tiling 的强制开关；实现 MxMatmul 时必须把场景识别落实到该 Host Tiling 调用。
<!-- cannbot:related:end -->
