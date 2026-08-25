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

- [Matmul高阶API开启IBShare模板共享B矩阵数据](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_b.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《MatmulTemplateParams》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [GetMMConfig](get_mm_config.md)（`related`）：GetMMConfig 生成可作为 MatmulTemplateParams 中 MatmulConfig 实参的自定义配置，连接配置选择与对象实例化。
- [GetNormalConfig](get_normal_config.md)（`related`）：GetNormalConfig 与《MatmulTemplateParams》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [Matmul Kernel侧接口](matmul_kernel.md)（`related`）：Matmul Kernel 入口说明对象通过模板参数和 MatmulConfig 绑定矩阵排布、dtype 与计算模式，正是 MatmulTemplateParams 的消费位置。
- [MatmulCallBackFunc](matmul_call_back_func.md)（`related`）：《MatmulCallBackFunc》说明模板参数，支持用户定制化Matmul的A、B、C矩阵搬入搬出功能，传入自定义回调函数指针替换默认搬运函数。；《MatmulTemplateParams》说明创建Matmul对象时需要传入的模板参数，包括A/B/C/Bias类型信息、MatmulConfig、MatmulCallBackFunc和MatmulPolicy。。二者在回调类型由Matmul模板参数、配置与Policy实例化，并经注册宏和用户自定义信息进入Kernel侧Matmul对象上存在可执行的直接衔接。
- [Matmul使用说明](matmul_usage.md)（`related`）：Matmul 使用说明给出 C=A*B+Bias 的操作数语义，可用于为 MatmulTemplateParams 的 A/B/C/Bias 类型参数选择正确矩阵角色。
- [GetMDLConfig](get_mdl_config.md)（`same_topic`）：GetMDLConfig 与《MatmulTemplateParams》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`same_topic`）：GetMatmulApiTiling 与《MatmulTemplateParams》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [MatmulConfig](matmul_config.md)（`same_topic`）：MatmulConfig 是 MatmulTemplateParams 的核心配置参数，决定 Norm、MDL、IBShare、BasicBlock 等执行模板。
- [MatmulPolicy](matmul_policy.md)（`same_topic`）：MatmulPolicy 是 MatmulTemplateParams 中用于替换扩展策略的模板参数，决定上/下三角、SplitM/SplitN 等内置模块。
- [SetBias](set_bias.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；MatmulTemplateParams正文说明“创建Matmul对象时需要传入的模板参数，包括A/B/C/Bias类型信息、MatmulConfig、MatmulCallBackFunc和MatmulPolicy”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
- [SetSelfDefineData](set_self_define_data.md)（`same_topic`）：SetSelfDefineData：SetSelfDefineData 只为 MatmulCallBackFunc 提供每次复用可更新的数据指针，模板声明决定回调契约，且正文明确要求它先于 SetTensorA/SetTensorB。 目标卡《MatmulTemplateParams》补充：创建Matmul对象时需要传入的模板参数，包括A/B/C/Bias类型信息、MatmulConfig、MatmulCallBackFunc和MatmulPolicy。
- [SetUserDefInfo](set_user_def_info.md)（`same_topic`）：SetUserDefInfo 与《MatmulTemplateParams》的实质衔接是：SetUserDefInfo 只在 MatmulCallBackFunc 使用 tilingPtr 时需要；SetSelfDefineData承载回调的可变数据，模板参数和使用说明决定回调是否启用。
<!-- cannbot:related:end -->
