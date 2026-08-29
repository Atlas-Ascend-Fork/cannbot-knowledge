---
type: API
title: MatmulTemplateParams
description: 创建Matmul对象时需要传入的模板参数，包括A/B/C/Bias类型信息、MatmulConfig、MatmulCallBackFunc和MatmulPolicy。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/Matmul_template_params.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# MatmulTemplateParams

创建Matmul对象时需要传入： - A、B、C、Bias的参数类型信息，类型信息通过MatmulType来定义，包括：内存逻辑位置、数据格式、数据类型、是否转置、数据排布和是否开启L1复用。 - MatmulConfig信息（可选），用于配置Matmul模板信息以及相关的配置参数。不配置默认使用Norm模板。

函数原型：
template <class A_TYPE, class B_TYPE, class C_TYPE, class BIAS_TYPE = C_TYPE, const auto& MM_CFG = CFG_NORM, class MM_CB = MatmulCallBackFunc<nullptr, nullptr, nullptr>, MATMUL_POLICY_DEFAULT_OF(MatmulPolicy)>
template <const auto& = MM_CFG, typename ...> \

参数：
- 参数（数据类型）：说明
- cfg（MatmulConfig）：Matmul模板的参数配置。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启MDL模板](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_mdl_template.md)（`explains`）：本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，开启MDL模板对算子性能的提升效果。在MDL模板中，MTE2流水从Global Memory到L1 Buffer（A1/B1）的数据搬运为一次性大包搬运，即一次MTE2能搬入多个Matmul计算的基本块，提升带宽利用率，使后续的MTE1流水尽可能复用A1/B1内基本块的缓存数据，减少MTE2的搬运次数。MDL模板的详细介绍请参考MatmulConfig。；创建Matmul对象时需要传入： - A、B、C、Bias的参数类型信息，类型信息通过MatmulType来定义，包括：内存逻辑位置、数据格式、数据类型、是否转置、数据排布和是否开启L1复用。 - MatmulConfig信息（可选），用于配置Matmul模板信息以及相关的配置参数。不配置默认使用Norm模板。；案例的 MDL 配置最终通过 Matmul 对象模板参数传入，目标补齐其与 A/B/C/Bias 类型信息的装配位置。
- [GetSpecialMDLConfig](get_special_mdl_config.md)（`related`）：返回值：MatmulConfig结构体。；MatmulConfig信息（可选），用于配置Matmul模板信息以及相关的配置参数。不配置默认使用Norm模板。；候选给出返回配置在创建 Matmul 对象时的消费位置与默认回退。
- [SetSelfDefineData](set_self_define_data.md)（`related`）：“class MM_CB = MatmulCallBackFunc<nullptr, nullptr, nullptr>”在创建 Matmul 对象时声明回调模板参数；“启用模板参数［MatmulCallBackFunc］(matmul_template_params.md#matmul-callback-func)（自定义回调函数）时”说明 SetSelfDefineData 是向该回调注入计算数据或 GM 地址的运行期入口。
- [MatmulCallBackFunc](matmul_call_back_func.md)（`same_topic`）：“通过模板参数MatmulCallBackFunc，传入实现的搬运函数的函数指针”定义回调定制方式，“MM_CB = MatmulCallBackFunc<nullptr, nullptr, nullptr>”给出该回调在 Matmul 模板参数中的实际槽位与默认值。
<!-- cannbot:related:end -->
