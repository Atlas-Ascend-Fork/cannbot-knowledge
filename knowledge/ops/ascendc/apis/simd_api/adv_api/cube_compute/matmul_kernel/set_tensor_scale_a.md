---
type: API
title: SetTensorScaleA
description: MxMatmul场景，设置矩阵乘中左矩阵的量化系数矩阵scaleA。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetTensorScaleA.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950']
---


# SetTensorScaleA

MxMatmul场景，设置矩阵乘中左矩阵的量化系数矩阵scaleA。

函数原型：
__aicore__ inline void SetTensorScaleA(const GlobalTensor<ScaleT>& gm, bool isTransposeScaleA = false);
__aicore__ inline void SetTensorScaleA(const LocalTensor<ScaleT>& leftMatrix, bool isTransposeScaleA = false);

参数：
- gm（输入）：量化系数scaleA矩阵。类型为GlobalTensor。支持的数据类型为：fp8_e8m0_t。
- leftMatrix（输入）：量化系数scaleA矩阵。类型为LocalTensor，支持的TPosition为TSCM/VECOUT。支持的数据类型为：fp8_e8m0_t。
- isTransposeScaleA（输入）：scaleA矩阵是否需要转置。 参数支持的取值如下：false：默认值，scaleA矩阵不转置。true：scaleA矩阵转置。 注意：scaleA矩阵为NZ格式时，该参数只支持取值为false。

约束：
- 传入的scaleA地址空间大小必须不小于singleCoreM*singleCoreK/32。
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。

支持：Ascend 950PR/Ascend 950DT。不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin X90、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [SetScaleAType](../matmul_tiling/set_scale_a_type.md)（`related`）：MxMatmul场景，设置矩阵乘中左矩阵的量化系数矩阵scaleA。；MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。；SetTensorScaleA 在 Kernel 侧提供 MxMatmul 的 scaleA 张量，SetScaleAType 在 Tiling 侧声明同一张量的位置、格式和转置，必须按同一合同配置。
<!-- cannbot:related:end -->
