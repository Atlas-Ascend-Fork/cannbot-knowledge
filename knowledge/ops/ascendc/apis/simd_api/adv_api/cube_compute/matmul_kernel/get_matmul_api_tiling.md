---
type: API
title: GetMatmulApiTiling
description: 在编译期间获取常量化的Matmul Tiling参数，减少Scalar计算开销，提升算子整体性能。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetMatmulApiTiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetMatmulApiTiling

本接口用于在编译期间获取常量化的Matmul Tiling参数。 Matmul Tiling常量化功能为在编译期期间获取常量化的Matmul Tiling参数并进行算子编译，从而减少Scalar计算开销，提升算子整体性能。具体为，在获取[Matmul模板](matmul_template_params.md)时，可以确定MatmulConfig的singleCore Shape（MatmulConfig中的singleCoreM/singleCoreN/singleCoreK）和Base Shape：[MatmulConfig中的basicM/basicN/basicK）参数，或者只确定Base Shape参数；通过指定获取模板的接口中的singleCore Shape和Base Shape参数，或者只指定Base Shape参数，获取自定义模板；然后调用本接口，得到常量化的Matmul Tiling参数。

函数原型：
template<class A_TYPE, class B_TYPE, class C_TYPE, class BIAS_TYPE>
__aicore__ constexpr MatmulApiStaticTiling GetMatmulApiTiling(const MatmulConfig& mmCFG, int32_t l1Size = Impl::L1_SIZE)

参数：
- A_TYPE（A矩阵类型信息，通过[MatmulType](matmul_usage.md#table1188045714378)来定义。
- B_TYPE：B矩阵类型信息，通过[MatmulType](matmul_usage.md#table1188045714378)来定义。
- C_TYPE：C矩阵类型信息，通过[MatmulType](matmul_usage.md#table1188045714378)来定义。
- BIAS_TYPE：BIAS矩阵类型信息，通过[MatmulType](matmul_usage.md#table1188045714378)来定义。
- mmCFG（输入）：获取的MatmulConfig模板。

返回值：[MatmulApiStaticTiling](matmul_template_params.md#table7939847143412)

约束：
- 入参mmCFG，在调用获取MatmulConfig模板的接口获取时，需要使用常数值指定(baseM, baseN, baseK)或者指定(baseM, baseN, baseK, singleCoreM, singleCoreN, singleCoreK\)，并且指定的参数值需要和Tiling计算的值保持一致。
- Batch Matmul场景支持全量常量化，但不支持使用空指针替代REGIST_MATMUL_OBJ的入参Tiling。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。
