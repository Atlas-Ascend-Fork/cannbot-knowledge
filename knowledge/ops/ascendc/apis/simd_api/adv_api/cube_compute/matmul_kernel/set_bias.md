---
type: API
title: SetBias
description: 设置矩阵乘的Bias。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetBias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetBias

设置矩阵乘的Bias。

函数原型：
__aicore__ inline void SetBias(const GlobalTensor<BiasT>& biasGlobal)
__aicore__ inline void SetBias(const LocalTensor<BiasT>& inputBias)

参数：
- biasGlobal（输入）：Bias矩阵。类型为GlobalTensor。不同型号支持的数据类型请参考支持的数据类型。 A矩阵、B矩阵、Bias支持的数据类型组合可参考Matmul输入输出数据类型的组合说明；在MxMatmul场景，A矩阵、B矩阵、Bias支持的数据类型组合可参考MatmulTypeWithScale参数说明。
- inputBias（输入）：Bias矩阵。类型为LocalTensor，支持的TPosition为TSCM/VECOUT。不同型号支持的数据类型请参考支持的数据类型。 A矩阵、B矩阵、Bias支持的数据类型组合可参考Matmul输入输出数据类型的组合说明；在MxMatmul场景，A矩阵、B矩阵、Bias支持的数据类型组合可参考MatmulTypeWithScale参数说明。

约束：
- 在Matmul Tiling计算中，必须配置TCubeTiling结构中的isBias参数为1，即启用Bias后，才能调用本接口设置Bias矩阵。
- 传入的Bias地址空间大小需要保证不小于singleN。
- 对于Ascend 950PR/Ascend 950DT，Bias矩阵的内存逻辑位置为TSCM且数据类型为float或int32_t时，Bias矩阵的LocalTensor空间必须64字节对齐。
- 支持的数据类型 Ascend 950PR/Ascend 950DT，支持的数据类型为：half、bfloat16_t、float、int32_t，其中仅在A、B的数据类型为int8_t时，Bias的数据类型可以设置为int32_t。 。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Batch Matmul复用Bias矩阵](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/batch_matmul_reuse_bias.md)（`explains`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；Batch Matmul复用Bias矩阵正文说明“Batch Matmul场景中各Batch使用相同Bias时，设置isBiasBatch为false复用单个不带Batch轴的Bias矩阵”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
- [ClearBias](clear_bias.md)（`related`）：SetBias 设置 Bias 输入，ClearBias/DisableBias 则撤销该参与标志；二者是同一 Matmul 对象 Bias 状态的相反控制动作。
- [DisableBias](disable_bias.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；DisableBias正文说明“清除Bias标志位，表示Matmul计算时没有Bias参与。如果在初始化时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
- [Init](init.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；Init正文说明“对Matmul对象的Tiling数据进行初始化，根据Tiling参数进行资源划分。Tiling参数可变场景下可多次调用”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
- [Iterate](iterate.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；Iterate正文说明“每调用一次计算一块baseM*baseN的C矩阵，内部维护迭代进度并偏移A、B矩阵首地址”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
- [MatmulTemplateParams](matmul_template_params.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；MatmulTemplateParams正文说明“创建Matmul对象时需要传入的模板参数，包括A/B/C/Bias类型信息、MatmulConfig、MatmulCallBackFunc和MatmulPolicy”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
- [Matmul使用说明](matmul_usage.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；Matmul使用说明正文说明“Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
- [SetBias](../matmul_tiling/set_bias.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；SetBias正文说明“EnableBias接口功能与该接口相同，建议使用EnableBias。 设置Bias是否参与运算”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
- [SetBiasType](../matmul_tiling/set_bias_type.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；SetBiasType正文说明“设置Bias的位置，数据格式，数据类型等信息，这些信息需要和kernel侧的设置保持一致”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
<!-- cannbot:related:end -->
