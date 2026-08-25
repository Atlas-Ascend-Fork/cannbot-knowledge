---
type: API
title: SetMadType
description: 设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetMadType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetMadType

设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。

参数：
- madType（输入）：设置Matmul模式。MatrixMadType类型，定义如下方代码所示，其中参数的含义为： MatrixMadType::NORMAL：普通模式，即非HF32模式、非MxMatmul场景。。

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [MxMatmul场景](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/mx_matmul_scenario.md)（`explains`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《MxMatmul场景》明确提供“带有量化系数的矩阵乘法，左右矩阵分别配有scaleA和scaleB量化系数矩阵，支持MXFP8、MXFP4等低位宽数据类型。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [Cube计算(ISASI)HF32](../../../basic_api/cube_compute/mmad_compute_key_features/hf32.md)（`related`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《Cube计算(ISASI)HF32》明确提供“HF32的核心功能体现为：用户在输入矩阵A、B矩阵都为fp32数据类型的场景下，当配置开启HF32开关后，fp32数据在执行矩阵乘法运算前会被转换并舍入为HF32（half-fp32）格式。这种做法可使Mmad（f322f32）接口的计算性能提升至原来的两倍，但会带来一定的精度损失。需要注意的是，尽管中间计算使用HF32格式，最终的运算结果仍以fp32格式输出，以保证后续处理的兼容性。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [GetTiling](get_tiling.md)（`related`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《GetTiling》明确提供“获取Tiling参数。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [Matmul Tiling类](matmul_tiling.md)（`related`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《Matmul Tiling类》明确提供“提供Matmul矩阵乘的Host侧Tiling类，包含TCubeTiling结构体、GetTiling及形状、类型、切分等参数设置方法。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`related`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《Matmul Tiling类使用说明》明确提供“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [TCubeTiling结构体](t_cube_tiling_struct.md)（`related`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《TCubeTiling结构体》明确提供“TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [基础APIHF32](../../../basic_api/cube_compute_tensor_api/mmad_compute_key_features/hf32.md)（`related`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《基础APIHF32》明确提供“HF32的核心功能体现为：用户在输入矩阵A和B都为fp32数据类型的场景下，当配置开启HF32开关后，fp32数据在执行矩阵乘法运算前会被转换并舍入为HF32（half-fp32）格式。这种做法可使Mmad（fp32->fp32）接口的计算性能提升至原来的两倍，但会带来一定的精度损失。需要注意的是，尽管中间计算使用HF32格式，最终的运算结果仍以fp32格式输出，以保证后续处理的兼容性。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [SetMatmulConfigParams](set_matmul_config_params.md)（`same_topic`）：《SetMadType》处理“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”。《SetMatmulConfigParams》明确提供“在计算Tiling时，用于自定义设置表1中的MatmulConfig参数。本接口中配置的参数对应的功能在Tiling与Kernel中需要保持一致，所以本接口中的参数取值，需要与Kernel侧对应的MatmulConfig参数值保持一致，详细MatmulConfig参数请见表2。”，其参数、调用或验证步骤直接接入Matmul 的 madType 配置、HF32/MxMatmul 模式及最终 Tiling 字段。
- [SetScaleAType](set_scale_a_type.md)（`same_topic`）：《SetScaleAType》处理“MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。”。《SetMadType》提供“设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。”，其具体合同或探针直接接入MxMatmul 的 scaleA 位置/格式、Kernel scale 张量、搬运和 Mx 模式启用合同。
<!-- cannbot:related:end -->
