---
type: API
title: SetTensorA
description: 设置矩阵乘的左矩阵A。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetTensorA.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetTensorA

设置矩阵乘的左矩阵A。

函数原型：
__aicore__ inline void SetTensorA(const GlobalTensor<SrcAT>& gm, bool isTransposeA = false)
__aicore__ inline void SetTensorA(const LocalTensor<SrcAT>& leftMatrix, bool isTransposeA = false)

参数：
- gm（输入）：A矩阵。类型为GlobalTensor。SrcAT参数表示A矩阵的数据类型。不同型号支持的数据类型请参考gm和leftMatrix支持的数据类型。
- leftMatrix（输入）：A矩阵。类型为LocalTensor，支持的TPosition为TSCM/VECOUT。SrcAT参数表示A矩阵的数据类型。不同型号支持的数据类型请参考gm和leftMatrix支持的数据类型 若设置TSCM首地址，默认矩阵可全载，已经位于TSCM，Iterate接口无需再进行GM->L1 Buffer（A1/B1）搬运。
- aScalar（输入）：A矩阵中设置的值。支持传入标量数据，标量数据会被扩展为一个形状为[1, K]的tensor参与矩阵乘计算，tensor的数值均为该标量值。例如，开发者可以通过将aScalar设置为1来实现矩阵B在K方向的reduce sum操作。
- isTransposeA（输入）：A矩阵是否需要转置。 注意：若A矩阵MatmulType的ISTRANS参数设置为true，该参数可以为true也可以为false，即运行时可以转置和非转置交替使用； 若A矩阵MatmulType的ISTRANS参数设置为false，该参数只能设置为false，若强行设置为true，精度会有异常；对于非half、非bfloat16_t输入类型的场景，为了确保Tiling侧与Kernel侧L1 Buffer空间计算大小保持一致及结果精度正确，该参数取值必须与Kernel侧定义A矩阵MatmulType的ISTRANS参数以及Tiling侧SetAType()接口的isTrans参数保持一致，即上述三个参数必须同时设置为true或同时设置为false。

约束：
- 传入的TensorA地址空间大小需要保证不小于singleM * singleK。
- gm和leftMatrix支持的数据类型 Ascend 950PR/Ascend 950DT，支持的数据类型为：half、bfloat16_t、int8_t、float、fp8_e4m3fn_t、fp8_e5m2_t、hifloat8_t。
- aScalar 支持的数据类型：Ascend 950PR/Ascend 950DT、Atlas A3 系列和 Atlas A2 系列均支持 half 与 float。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [TSCM输入的矩阵乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/tscm_input_matmul.md)（`explains`）：TSCM输入的矩阵乘说明用户自行管理TSCM内存空间，Matmul直接使用传入的TSCM地址，不进行GM到TSCM的数据搬入。
- [SetAType](../matmul_tiling/set_a_type.md)（`related`）：SetAType 与《SetTensorA》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [SetSelfDefineData](set_self_define_data.md)（`related`）：SetSelfDefineData：SetSelfDefineData 只为 MatmulCallBackFunc 提供每次复用可更新的数据指针，模板声明决定回调契约，且正文明确要求它先于 SetTensorA/SetTensorB。 目标卡《SetTensorA》补充：设置矩阵乘的左矩阵A。
- [SetTensorB](set_tensor_b.md)（`related`）：SetTensorB 与《SetTensorA》的衔接是：SetTensorB 的地址范围和转置解释同时受 SetOrgShape、Tiling侧 SetBType/ISTRANS 约束；Matmul 使用流程还要求与 SetTensorA 成对准备输入。
- [SetTensorScaleA](set_tensor_scale_a.md)（`related`）：SetTensorScaleA 为左矩阵 A 提供量化系数，且其 singleCoreM*singleCoreK 容量与 SetTensorA 的 singleM*singleK 数据域相对应；实现量化 MxMatmul 时需要成对设置。
- [Init](init.md)（`same_topic`）：Init说明对Matmul对象的Tiling数据进行初始化，根据Tiling参数进行资源划分。Tiling参数可变场景下可多次调用。
- [Iterate](iterate.md)（`same_topic`）：Iterate说明每调用一次计算一块baseM*baseN的C矩阵，内部维护迭代进度并偏移A、B矩阵首地址。
- [Matmul Kernel侧接口](matmul_kernel.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“SetTensorA”明确设置矩阵乘的左矩阵A。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
- [Matmul使用说明](matmul_usage.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；SetTensorA正文界定“设置矩阵乘的左矩阵A”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
<!-- cannbot:related:end -->
