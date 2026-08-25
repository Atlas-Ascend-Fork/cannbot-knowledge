---
type: API
title: SetAType
description: 设置A矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetAType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetAType

设置A矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。

参数：
- pos（输入）：A矩阵所在的buffer位置，可设置为：TPosition::GM, TPosition::VECOUT, TPosition::TSCM。
- type（输入）：A矩阵的数据格式，可设置为：CubeFormat::ND，CubeFormat::NZ，CubeFormat::VECTOR。
- dataType（输入）：A矩阵的数据类型，可设置为：DataType::DT_FLOAT、DataType::DT_FLOAT16、DataType::DT_BFLOAT16、DataType::DT_INT8、DataType::DT_INT4、DataType::DT_FLOAT8_E4M3FN、DataType::DT_FLOAT8_E5M2、DataType::DT_HIFLOAT8。
- isTrans（输入）：A矩阵是否转置。 参数取值：true：A矩阵转置；false：A矩阵不转置。

返回值：-1表示设置失败；0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [使用高阶API时配套的Tiling实现](../../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_with_advanced_api.md)（`explains`）：SetAType 与《使用高阶API时配套的Tiling实现》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [Matmul Tiling类](matmul_tiling.md)（`related`）：SetAType 与《Matmul Tiling类》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`related`）：SetAType 与《Matmul Tiling类使用说明》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [Matmul Tiling类构造函数](matmul_tiling_constructor.md)（`related`）：SetAType 与《Matmul Tiling类构造函数》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [SetALayout](set_a_layout.md)（`related`）：SetALayout 负责“设置A矩阵的Layout轴信息，包括B、S、N、G、D轴。对于BSNGD、SBNGD、BNGS1S2 Layout格式，调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置A矩阵的Layout轴信息”；SetAType 负责“设置A矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致”。
- [SetBType](set_b_type.md)（`related`）：SetAType 与《SetBType》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [SetTensorA](../matmul_kernel/set_tensor_a.md)（`related`）：SetAType 与《SetTensorA》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [TensorDataType](../../data_structures/tensor_data_type.md)（`related`）：TensorDataType 与《SetAType》的实质衔接是：TensorDataType 与 TensorShape 都是高阶 API Host Tiling 公共类型；SetAType 的 dataType 参数展示该 ge::DataType 别名如何进入矩阵类型配置。
- [SetScaleAType](set_scale_a_type.md)（`same_topic`）：《SetScaleAType》处理“MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。”。《SetAType》提供“设置A矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。”，其具体合同或探针直接接入MxMatmul 的 scaleA 位置/格式、Kernel scale 张量、搬运和 Mx 模式启用合同。
<!-- cannbot:related:end -->
