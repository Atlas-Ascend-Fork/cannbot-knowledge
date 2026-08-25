---
type: API
title: SetBType
description: 设置B矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetBType

设置B矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。

参数：
- pos（输入）：B矩阵所在的buffer位置，可设置为：TPosition::GM, TPosition::VECOUT, TPosition::TSCM。
- type（输入）：B矩阵的数据格式，可设置为：CubeFormat::ND，CubeFormat::NZ。
- dataType（输入）：B矩阵的数据类型，可设置为：DataType::DT_FLOAT、DataType::DT_FLOAT16、DataType::DT_BFLOAT16 、DataType::DT_INT8、DataType::DT_INT4、DataType::DT_FLOAT8_E4M3FN、DataType::DT_FLOAT8_E5M2、DataType::DT_HIFLOAT8。
- isTrans（输入）：B矩阵是否转置。 参数取值：true：B矩阵转置；false：B矩阵不转置。

返回值：-1表示设置失败；0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [使用高阶API时配套的Tiling实现](../../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_with_advanced_api.md)（`explains`）：示例用 SetBType 将右矩阵 B 的位置、格式和 dtype 写入 Matmul Tiling 对象，K 维与格式校验依赖这份配置。
- [SetAType](set_a_type.md)（`related`）：SetAType 与《SetBType》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [SetBLayout](set_b_layout.md)（`related`）：《SetBType》明确“设置B矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。”；它与《SetBLayout》的“设置B矩阵的Layout轴信息，包括B、S、N、G、D轴。对于BSNGD、SBNGD、BNGS1S2 Layout格式，调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置B矩阵的Layout轴信息。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetTensorB](../matmul_kernel/set_tensor_b.md)（`related`）：SetTensorB 与《SetBType》的衔接是：SetTensorB 的地址范围和转置解释同时受 SetOrgShape、Tiling侧 SetBType/ISTRANS 约束；Matmul 使用流程还要求与 SetTensorA 成对准备输入。
<!-- cannbot:related:end -->
