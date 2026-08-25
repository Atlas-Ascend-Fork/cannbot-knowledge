---
type: API
title: SetScaleBType
description: MxMatmul场景，设置scaleB矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleB矩阵的信息将与SetBType中设置的B矩阵的信息保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetScaleBType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetScaleBType

MxMatmul场景，设置scaleB矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleB矩阵的信息将与SetBType中设置的B矩阵的信息保持一致。

参数：
- scalePos（输入）：scaleB矩阵的内存逻辑位置。
- scaleType（输入）：scaleB矩阵的物理排布格式。
- isScaleTrans（输入）：scaleB矩阵是否转置。参数支持的取值如下：true：默认值，scaleB矩阵转置；/false：scaleB矩阵不转置。

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [MxMatmul场景](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/mx_matmul_scenario.md)（`explains`）：MxMatmul场景 与《SetScaleBType》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [SetTensorScaleB](../matmul_kernel/set_tensor_scale_b.md)（`related`）：Host 侧 SetScaleBType 声明 scaleB 数据类型，Kernel 侧 SetTensorScaleB 注入对应 scaleB 张量，二者共同构成 MX Matmul 的缩放输入契约。
- [SetScaleAType](set_scale_a_type.md)（`same_topic`）：《SetScaleAType》处理“MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。”。《SetScaleBType》提供“MxMatmul场景，设置scaleB矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleB矩阵的信息将与SetBType中设置的B矩阵的信息保持一致。”，其具体合同或探针直接接入MxMatmul 的 scaleA 位置/格式、Kernel scale 张量、搬运和 Mx 模式启用合同。
<!-- cannbot:related:end -->
