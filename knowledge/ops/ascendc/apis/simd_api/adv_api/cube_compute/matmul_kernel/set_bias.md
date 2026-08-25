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
