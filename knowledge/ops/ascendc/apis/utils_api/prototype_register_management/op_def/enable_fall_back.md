---
type: API
title: EnableFallBack
description: 通过本接口启用fallback配置，启用后将自动生成一个fallback函数并注册给GE。fallback函数的核心逻辑是将GE的输入、输出及属性转换为aclnn单算子API所需的参数格式，随后调用aclnn接口。动态图场景下，GE可直接调用fallback函数（函数中调用了aclnn接口），从而简化调度流程。关于fallback下发算子的详细介绍请参考《图开发》。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/EnableFallBack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# EnableFallBack

## 功能说明
通过本接口启用fallback配置，启用后将自动生成一个fallback函数并注册给GE。fallback函数的核心逻辑是将GE的输入、输出及属性转换为aclnn单算子API所需的参数格式，随后调用aclnn接口。动态图场景下，GE可直接调用fallback函数（函数中调用了aclnn接口），从而简化调度流程。关于fallback下发算子的详细介绍请参考《图开发》。
## 函数原型
## 参数说明
无
## 返回值说明
OpDef算子定义，OpDef请参考OpDef。
## 约束说明
-   算子需要注册并实现InferShape函数。
-   算子需要注册并实现InferDataType函数。

<!-- cannbot:related:start -->
## 相关

- [InferShape 返回 identity 致空 kernel 假通过](../../../../runbooks/precision/infershape_identity_kernel.md)（`exemplifies`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；InferShape 返回 identity 致空 kernel 假通过正文界定“op_host InferShape 用 *output=*input 占位时，aclnn 框架对 identity 用例走旁路 copy，空 kernel 也有用例通过，掩盖 kernel 未输出的缺陷”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
- [optional input 未连接触发 InferShape 失败](../../../../runbooks/compilation/optional_input_infershape.md)（`exemplifies`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；optional input 未连接触发 InferShape 失败正文界定“OpDef 声明含 optional input、GEIR 图未连接该 input 时，GE 在 InferShape pass 的 ConstructInferShapeContextInputs 阶段 assert 失败，算子 Infe”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
- [缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape](../../../../runbooks/compilation/op_proto_lib_axes_infershape.md)（`exemplifies`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape正文界定“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferSha”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
- [ExtendCfgInfo](../op_ai_core_config/extend_cfg_info.md)（`related`）：ExtendCfgInfo 的 aclnnSupport.value 明确以 EnableFallBack 为默认 support_aclnn 触发来源；前者细化静态/动态下发策略，后者生成并注册实际 fallback 函数。
- [OpDef](op_def.md)（`same_topic`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；OpDef正文界定“OpDef算子定义接口索引”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
- [Output（OpDef）](output.md)（`same_topic`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；Output（OpDef）正文界定“注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
- [SetInferDataType](set_infer_data_type.md)（`same_topic`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；SetInferDataType正文界定“使用图模式时，需要调用该接口注册DataType推导函数”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
- [SetInferShape](set_infer_shape.md)（`same_topic`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；SetInferShape正文界定“使用图模式时，需要调用该接口注册Shape推导函数”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
- [原型注册接口（OP_ADD）](../op_add.md)（`same_topic`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；原型注册接口（OP_ADD）正文界定“注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
<!-- cannbot:related:end -->
