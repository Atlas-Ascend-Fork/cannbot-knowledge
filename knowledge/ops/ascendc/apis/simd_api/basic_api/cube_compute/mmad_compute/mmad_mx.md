---
type: API
title: MmadMx
description: 带量化系数的矩阵乘法接口，左右矩阵各有对应量化系数矩阵，实现C=(scaleA⊗A)*(scaleB⊗B)+Bias。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/MmadMx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# MmadMx

Microscaling 矩阵乘加接口，实现 C=(scaleA⊗A)×(scaleB⊗B)+Bias。K 方向每 32 个元素共享一个量化因子。头文件 `basic_api/kernel_operator_mm_intf.h`。

矩阵布局：A（L0A，M×K，Nz）、scaleA（L0A_MX，M×K/32，小z shape(2,16)）、B（L0B，K×N，Zn）、scaleB（L0B_MX，K/32×N，小n shape(2,16)）、C（L0C，M×N，Nz）、Bias（1×N）。支持带/不带 bias 两个原型，mmadParams 为 MmadParams 结构体。仅 Ascend 950PR/950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [MxMatmul场景](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/mx_matmul_scenario.md)（`explains`）：MxMatmul场景 与《MmadMx》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [AscMmadMx](../../../c_api/cube_compute/asc_mmad_mx.md)（`same_topic`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《MmadMx》说明带量化系数的矩阵乘法接口，左右矩阵各有对应量化系数矩阵，实现C=(scaleA⊗A)*(scaleB⊗B)+Bias。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
- [SetScaleAType](../../../adv_api/cube_compute/matmul_tiling/set_scale_a_type.md)（`same_topic`）：《SetScaleAType》处理“MxMatmul场景，设置scaleA矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。”。《MmadMx》提供“带量化系数的矩阵乘法接口，左右矩阵各有对应量化系数矩阵，实现C=(scaleA⊗A)*(scaleB⊗B)+Bias。”，其具体合同或探针直接接入MxMatmul 的 scaleA 位置/格式、Kernel scale 张量、搬运和 Mx 模式启用合同。
<!-- cannbot:related:end -->
