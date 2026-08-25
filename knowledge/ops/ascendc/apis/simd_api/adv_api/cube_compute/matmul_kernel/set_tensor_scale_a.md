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

- [MxMatmul场景](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/mx_matmul_scenario.md)（`explains`）：MxMatmul场景 与《SetTensorScaleA》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [AscMmadMx](../../../c_api/cube_compute/asc_mmad_mx.md)（`related`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《SetTensorScaleA》说明MxMatmul场景，设置矩阵乘中左矩阵的量化系数矩阵scaleA。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
- [CopyL1ToL0ScaleA](../../../basic_api/cube_compute_tensor_api/cube_compute_load/copy_l1_to_l0_scale_a.md)（`related`）：CopyL1ToL0ScaleA 把 A 的量化 scale 搬入 L0ScaleA，而 SetTensorScaleA 绑定该 scale 张量；绑定必须先于迭代中的 scale 搬运。
- [SetScaleAType](../matmul_tiling/set_scale_a_type.md)（`related`）：Kernel 侧 SetTensorScaleA 的位置、格式和转置必须与 Tiling 侧 SetScaleAType 保持一致；目标卡还说明未调用时会继承 SetAType，是直接的 Host/Kernel 契约。
- [SetTensorA](set_tensor_a.md)（`related`）：SetTensorScaleA 为左矩阵 A 提供量化系数，且其 singleCoreM*singleCoreK 容量与 SetTensorA 的 singleM*singleK 数据域相对应；实现量化 MxMatmul 时需要成对设置。
- [SetTensorScaleB](set_tensor_scale_b.md)（`related`）：MxMatmul 量化需分别绑定左右矩阵的 scaleA/scaleB；两接口的矩阵侧别必须与 A/B 输入对应。
<!-- cannbot:related:end -->
