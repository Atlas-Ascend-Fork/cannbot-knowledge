---
type: API
title: SetTensorScaleB
description: MxMatmul场景，设置矩阵乘中右矩阵的量化系数矩阵scaleB。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetTensorScaleB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950']
---


# SetTensorScaleB

MxMatmul场景，设置矩阵乘中右矩阵的量化系数矩阵scaleB。

函数原型：
__aicore__ inline void SetTensorScaleB(const GlobalTensor<ScaleT>& gm, bool isTransposeScaleB = true);
__aicore__ inline void SetTensorScaleB(const LocalTensor<ScaleT>& rightMatrix, bool isTransposeScaleB = true);

参数：
- gm（输入）：量化系数scaleB矩阵。类型为GlobalTensor。支持的数据类型为：fp8_e8m0_t。
- rightMatrix（输入）：量化系数scaleB矩阵。类型为LocalTensor，支持的TPosition为TSCM/VECOUT。支持的数据类型为：fp8_e8m0_t。
- isTransposeScaleB（输入）：scaleB矩阵是否需要转置。 参数支持的取值如下：false：scaleB矩阵不转置。true：默认值，scaleB矩阵转置。 注意：scaleB矩阵为NZ格式时，该参数只支持取值为true。

约束：
- 传入的scaleB地址空间大小必须不小于singleCoreK*singleCoreN/32。
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。

支持：Ascend 950PR/Ascend 950DT。不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin X90、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [SetScaleBType](../matmul_tiling/set_scale_b_type.md)（`related`）：MxMatmul场景，设置矩阵乘中右矩阵的量化系数矩阵scaleB。；MxMatmul场景，设置scaleB矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleB矩阵的信息将与SetBType中设置的B矩阵的信息保持一致。；Kernel 侧 SetTensorScaleB 绑定 scaleB 张量和转置方式，Host Tiling 侧 SetScaleBType 描述同一 scaleB 的位置、排布与转置，二者参数必须一致才能闭合 MxMatmul 配置。
<!-- cannbot:related:end -->
