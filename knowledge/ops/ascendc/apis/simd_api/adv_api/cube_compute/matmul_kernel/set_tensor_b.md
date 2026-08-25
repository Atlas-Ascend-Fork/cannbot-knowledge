---
type: API
title: SetTensorB
description: 设置矩阵乘的右矩阵B。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetTensorB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetTensorB

设置矩阵乘的右矩阵B。

函数原型：
__aicore__ inline void SetTensorB(const GlobalTensor<SrcBT>& gm, bool isTransposeB = false)
__aicore__ inline void SetTensorB(const LocalTensor<SrcBT>& rightMatrix, bool isTransposeB = false)

参数：
- SrcBT：操作数的数据类型。
- gm（输入）：B矩阵。类型为GlobalTensor。SrcBT参数表示B矩阵的数据类型。 不同型号支持的数据类型请参考gm和rightMatrix支持的数据类型。
- rightMatrix（输入）：B矩阵。类型为LocalTensor，支持的TPosition为TSCM/VECOUT。SrcBT参数表示B矩阵的数据类型。 不同型号支持的数据类型请参考gm和rightMatrix支持的数据类型。
- bScalar（输入）：B矩阵中设置的值。支持传入标量数据，标量数据会被扩展为一个形状为[1, K]的tensor参与矩阵乘计算，tensor的数值均为该标量值。例如，开发者可以通过将bScalar设置为1来实现矩阵A在K方向的reduce sum操作。
- isTransposeB（输入）：B矩阵是否需要转置。 注意：若B矩阵MatmulType的ISTRANS参数设置为true，该参数可以为true也可以为false，即运行时可以转置和非转置交替使用； 若B矩阵MatmulType的ISTRANS参数设置为false，该参数只能设置为false，若强行设置为true，精度会有异常；对于非half、非bfloat16_t输入类型的场景，为了确保Tiling侧与Kernel侧L1 Buffer空间计算大小保持一致及结果精度正确，该参数取值必须与Kernel侧定义B矩阵MatmulType的ISTRANS参数以及Tiling侧SetBType()接口的isTrans参数保持一致，即上述三个参数必须同时设置为true或同时设置为false。

约束：
- 传入的TensorB地址空间大小需要保证不小于singleK * singleN。
- gm和rightMatrix支持的数据类型 Ascend 950PR/Ascend 950DT，支持的数据类型为：half、bfloat16_t、int8_t、float、fp8_e4m3fn_t、fp8_e5m2_t、hifloat8_t。
- bScalar 支持的数据类型：Ascend 950PR/Ascend 950DT、Atlas A3 系列和 Atlas A2 系列均支持 half 与 float。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Matmul使用说明](matmul_usage.md)（`related`）：SetTensorB 与《Matmul使用说明》的衔接是：SetTensorB 的地址范围和转置解释同时受 SetOrgShape、Tiling侧 SetBType/ISTRANS 约束；Matmul 使用流程还要求与 SetTensorA 成对准备输入。
- [SetBType](../matmul_tiling/set_b_type.md)（`related`）：SetTensorB 与《SetBType》的衔接是：SetTensorB 的地址范围和转置解释同时受 SetOrgShape、Tiling侧 SetBType/ISTRANS 约束；Matmul 使用流程还要求与 SetTensorA 成对准备输入。
- [SetOrgShape](set_org_shape.md)（`related`）：SetTensorB 与《SetOrgShape》的衔接是：SetTensorB 的地址范围和转置解释同时受 SetOrgShape、Tiling侧 SetBType/ISTRANS 约束；Matmul 使用流程还要求与 SetTensorA 成对准备输入。
- [SetSelfDefineData](set_self_define_data.md)（`related`）：SetSelfDefineData：SetSelfDefineData 只为 MatmulCallBackFunc 提供每次复用可更新的数据指针，模板声明决定回调契约，且正文明确要求它先于 SetTensorA/SetTensorB。 目标卡《SetTensorB》补充：设置矩阵乘的右矩阵B。
- [SetTensorA](set_tensor_a.md)（`related`）：SetTensorB 与《SetTensorA》的衔接是：SetTensorB 的地址范围和转置解释同时受 SetOrgShape、Tiling侧 SetBType/ISTRANS 约束；Matmul 使用流程还要求与 SetTensorA 成对准备输入。
- [SetTensorScaleB](set_tensor_scale_b.md)（`related`）：SetTensorB 绑定右矩阵数据，而 SetTensorScaleB 绑定其量化系数；二者共同决定 B 路径的输入和缩放。
- [Matmul Kernel侧接口](matmul_kernel.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“SetTensorB”明确设置矩阵乘的右矩阵B。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
<!-- cannbot:related:end -->
