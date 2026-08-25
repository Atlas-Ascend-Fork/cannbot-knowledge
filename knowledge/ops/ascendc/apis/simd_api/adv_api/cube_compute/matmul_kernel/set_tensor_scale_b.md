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

- [MxMatmul场景](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/mx_matmul_scenario.md)（`explains`）：MxMatmul场景 与《SetTensorScaleB》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [AscMmadMx](../../../c_api/cube_compute/asc_mmad_mx.md)（`related`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《SetTensorScaleB》说明MxMatmul场景，设置矩阵乘中右矩阵的量化系数矩阵scaleB。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
- [CopyL1ToL0ScaleB](../../../basic_api/cube_compute_tensor_api/cube_compute_load/copy_l1_to_l0_scale_b.md)（`related`）：Tensor API 的 CopyL1ToL0ScaleB 说明 scaleB 在 L1 到 L0ScaleB 的物理搬运要求，补充 SetTensorScaleB 绑定后的数据通路。
- [SetScaleBType](../matmul_tiling/set_scale_b_type.md)（`related`）：Host 侧 SetScaleBType 声明 scaleB 数据类型，Kernel 侧 SetTensorScaleB 注入对应 scaleB 张量，二者共同构成 MX Matmul 的缩放输入契约。
- [SetTensorB](set_tensor_b.md)（`related`）：SetTensorB 绑定右矩阵数据，而 SetTensorScaleB 绑定其量化系数；二者共同决定 B 路径的输入和缩放。
- [SetTensorScaleA](set_tensor_scale_a.md)（`related`）：MxMatmul 量化需分别绑定左右矩阵的 scaleA/scaleB；两接口的矩阵侧别必须与 A/B 输入对应。
<!-- cannbot:related:end -->
