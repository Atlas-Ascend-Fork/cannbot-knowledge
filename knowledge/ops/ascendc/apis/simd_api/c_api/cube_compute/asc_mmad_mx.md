---
type: API
title: AscMmadMx
description: 完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_mmad_mx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscMmadMx

本接口用于完成带有量化系数的矩阵乘加计算（MmadMx），即左矩阵A和右矩阵B均有对应的量化系数矩阵，左量化系数矩阵ScaleA和右量化系数矩阵ScaleB。在MmadMx场景中，左量化系数矩阵与左矩阵相乘，右量化系数矩阵与右矩阵相乘，然后对两个乘积的结果做矩阵乘法。
本接口不单独传入Scale矩阵地址，而是根据A、B矩阵的起始地址，按照固定的地址映射关系从L0A_MX Buffer和L0B_MX Buffer读取对应的Scale矩阵。各矩阵的信息说明

当矩阵数据类型为fp8_e5m2_t、fp8_e4m3fn_t时，K0 = 32；当矩阵数据类型为fp4x2_e2m1_t、fp4x2_e1m2_t时，K0 = 64。

本接口为矩阵计算接口，仅在AIC上生效。

参数：c_matrix(输出): 目的操作数，结果矩阵C在L0C Buffer中的起始地址，数据类型为float，需按照1024字节对齐。；a_matrix(输入): 源操作数，左矩阵A在L0A Buffer中的起始地址。数据类型由接口重载决定，具体请参见表2。 矩阵数据类型为fp4x2_e2m1_t、fp4x2_e1m2_t时需按照512字节对齐，矩阵数据类型为fp8_e5m2_t、fp8_e4m3fn_t时需按照1024字节对齐。 ScaleA矩阵在L0A_MX Buffer中的起始地址为a_matrix起始地址除以16。；b_matrix(输入): 源操作数，右矩阵B在L0B Buffer中的起始地址。数据类型由接口重载决定，具体请参见表2。 矩阵数据类型为fp4x2_e2m1_t、fp4x2_e1m2_t时需按照512字节对齐，矩阵数据类型为fp8_e5m2_t、fp8_e4m3fn_t时需按照1024字节对齐。 ScaleB矩阵在L0B_MX Buffer中的起始地址为b_matrix起始地址除以16。；left_height(输入): 左矩阵A和结果矩阵C的M维大小，单位为元素，取值范围为[0, 4095]。；n_dim(输入): 左矩阵A和右矩阵B的K维大小，单位为元素，取值范围为[0, 4095]，并且需为64的倍数。；right_width(输入): 右矩阵B和结果矩阵C的N维大小，单位为元素，取值范围为[0, 4095]。

约束：- 本接口仅在AIC上生效，在AIV上调用将直接返回。
- left_height、n_dim、right_width中的任意一个值为0时，接口将被视为NOP（空操作）。
- 调用本接口前，需通过asc_copy_l12l0a_mx和asc_copy_l12l0b_mx等接口，将ScaleA和ScaleB矩阵分别搬入L0A_MX Buffer和L0B_MX Buffer。ScaleA和ScaleB矩阵的数据类型必须为fp8_e8m0_t，K方向上每个Scale元素对应32个输入矩阵元素。

- 内存使用约束说明

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [MxMatmul场景](../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/mx_matmul_scenario.md)（`explains`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《MxMatmul场景》说明带有量化系数的矩阵乘法，左右矩阵分别配有scaleA和scaleB量化系数矩阵，支持MXFP8、MXFP4等低位宽数据类型。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
- [AscCopyL12l0aMx](../cube_data_move/asc_copy_l12l0a_mx.md)（`related`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《AscCopyL12l0aMx》说明将Mx scale矩阵从L1 Buffer搬运到L0A Buffer。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
- [AscCopyL12l0bMx](../cube_data_move/asc_copy_l12l0b_mx.md)（`related`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《AscCopyL12l0bMx》说明将Mx scale矩阵从L1 Buffer搬运到L0B Buffer。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
- [SetTensorScaleA](../../adv_api/cube_compute/matmul_kernel/set_tensor_scale_a.md)（`related`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《SetTensorScaleA》说明MxMatmul场景，设置矩阵乘中左矩阵的量化系数矩阵scaleA。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
- [SetTensorScaleB](../../adv_api/cube_compute/matmul_kernel/set_tensor_scale_b.md)（`related`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《SetTensorScaleB》说明MxMatmul场景，设置矩阵乘中右矩阵的量化系数矩阵scaleB。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
- [MmadMx](../../basic_api/cube_compute/mmad_compute/mmad_mx.md)（`same_topic`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《MmadMx》说明带量化系数的矩阵乘法接口，左右矩阵各有对应量化系数矩阵，实现C=(scaleA⊗A)*(scaleB⊗B)+Bias。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
<!-- cannbot:related:end -->
