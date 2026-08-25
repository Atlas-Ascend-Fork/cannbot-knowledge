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

- [AscMmadMx](../../../../../apis/simd_api/c_api/cube_compute/asc_mmad_mx.md)（`explains`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《MxMatmul场景》说明带有量化系数的矩阵乘法，左右矩阵分别配有scaleA和scaleB量化系数矩阵，支持MXFP8、MXFP4等低位宽数据类型。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
- [MmadMx](../../../../../apis/simd_api/basic_api/cube_compute/mmad_compute/mmad_mx.md)（`explains`）：MxMatmul场景 与《MmadMx》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [SetMadType](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_mad_type.md)（`explains`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《MxMatmul场景》明确提供“带有量化系数的矩阵乘法，左右矩阵分别配有scaleA和scaleB量化系数矩阵，支持MXFP8、MXFP4等低位宽数据类型。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [SetScaleAType](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_scale_a_type.md)（`explains`）：《SetScaleAType》处理“MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。”。《MxMatmul场景》提供“带有量化系数的矩阵乘法，左右矩阵分别配有scaleA和scaleB量化系数矩阵，支持MXFP8、MXFP4等低位宽数据类型。”，其具体合同或探针直接接入MxMatmul 的 scaleA 位置/格式、Kernel scale 张量、搬运和 Mx 模式启用合同。
- [SetScaleBType](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_scale_b_type.md)（`explains`）：MxMatmul场景 与《SetScaleBType》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [SetSingleShape](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_single_shape.md)（`explains`）：MxMatmul场景 与《SetSingleShape》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [SetTensorScaleA](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_tensor_scale_a.md)（`explains`）：MxMatmul场景 与《SetTensorScaleA》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [SetTensorScaleB](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_tensor_scale_b.md)（`explains`）：MxMatmul场景 与《SetTensorScaleB》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [Matmul特性介绍](matmul_features.md)（`same_topic`）：MxMatmul场景 与《Matmul特性介绍》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [矩阵乘输出的量化/反量化](matmul_output_quant_dequant.md)（`same_topic`）：MxMatmul场景 与《矩阵乘输出的量化/反量化》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [矩阵向量乘](matrix_vector_multiply.md)（`same_topic`）：矩阵向量乘 与《MxMatmul场景》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
<!-- cannbot:related:end -->
