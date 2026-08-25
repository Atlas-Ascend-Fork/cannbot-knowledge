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

<!-- cannbot:related:start -->
## 相关

- [Matmul算子优化Tiling策略](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_strategy.md)（`explains`）：GetMatmulApiTiling 与《Matmul算子优化Tiling策略》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [Matmul高阶API开启IBShare模板共享B矩阵数据](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_b.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《GetMatmulApiTiling》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [Matmul高阶API开启Tiling全量常量化](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_constant.md)（`explains`）：GetMatmulApiTiling 与《Matmul高阶API开启Tiling全量常量化》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [含有Matmul高阶API的算子精度问题](../../../../../guides/programming_guide/appendix/faq/matmul_advanced_api_precision.md)（`explains`）：GetMatmulApiTiling 与《含有Matmul高阶API的算子精度问题》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [GetBasicConfig](get_basic_config.md)（`related`）：GetMatmulApiTiling 生成 GetBasicConfig 所要求一致的 TCubeTiling；两者共同约束 baseM/baseN/baseK 与单核切分的匹配。
- [GetNormalConfig](get_normal_config.md)（`related`）：GetNormalConfig 与《GetMatmulApiTiling》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [GetSpecialMDLConfig](get_special_mdl_config.md)（`related`）：GetMatmulApiTiling 与《GetSpecialMDLConfig》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [Init](init.md)（`related`）：Host/编译期生成的 Matmul tiling 参数是 Init 在 Kernel 侧划分资源的直接输入，常量化路径还能减少 Scalar 开销。
- [MatmulGetTmpBufSize](../get_matmul_compute_space/matmul_get_tmp_buf_size.md)（`related`）：GetMatmulApiTiling 与《MatmulGetTmpBufSize》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [MatmulGetTmpBufSizeV2](../get_matmul_compute_space/matmul_get_tmp_buf_size_v2.md)（`related`）：GetMatmulApiTiling 与《MatmulGetTmpBufSizeV2》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [REGIST_MATMUL_OBJ](regist_matmul_obj.md)（`related`）：REGIST_MATMUL_OBJ 要求传入 TCubeTiling；GetMatmulApiTiling 是 Host 侧获得这一 tiling 的配套入口。
- [GetMDLConfig](get_mdl_config.md)（`same_topic`）：GetMDLConfig 与《GetMatmulApiTiling》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [MatmulConfig](matmul_config.md)（`same_topic`）：GetMatmulApiTiling 与《MatmulConfig》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [MatmulTemplateParams](matmul_template_params.md)（`same_topic`）：GetMatmulApiTiling 与《MatmulTemplateParams》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [Matmul使用说明](matmul_usage.md)（`same_topic`）：GetMatmulApiTiling 与《Matmul使用说明》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [SetMatmulConfigParams](../matmul_tiling/set_matmul_config_params.md)（`same_topic`）：GetMatmulApiTiling 与《SetMatmulConfigParams》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
<!-- cannbot:related:end -->
