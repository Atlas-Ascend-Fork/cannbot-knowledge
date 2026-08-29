---
type: API
title: SetScaleAType
description: MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetScaleAType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetScaleAType

MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。

参数：
- scalePos（输入）：scaleA矩阵的内存逻辑位置。
- scaleType（输入）：scaleA矩阵的物理排布格式。
- isScaleTrans（输入）：scaleA矩阵是否转置。参数支持的取值如下：true：scaleA矩阵转置；/false：默认值，scaleA矩阵不转置。

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [SetAType](set_a_type.md)（`related`）：设置A矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。；如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。。SetScaleAType 的缺省描述直接继承 SetAType 的 A 矩阵描述，因此配置 scaleA 时必须理解 SetAType 的位置、格式、类型和转置合同，但两接口仍配置不同操作数。
- [SetTensorScaleA](../matmul_kernel/set_tensor_scale_a.md)（`related`）：MxMatmul场景，设置矩阵乘中左矩阵的量化系数矩阵scaleA。；MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。；SetTensorScaleA 在 Kernel 侧提供 MxMatmul 的 scaleA 张量，SetScaleAType 在 Tiling 侧声明同一张量的位置、格式和转置，必须按同一合同配置。
<!-- cannbot:related:end -->
