---
type: API
title: Input（原型注册管理）
description: 某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreConfig/Input.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Input

## 功能说明
某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。
通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。
## 函数原型
## 参数说明
## 返回值说明
算子参数定义，OpParamDef请参考OpParamDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《ACLNN 561000 非连续张量需 AutoContiguous》明确“aclnn 算子仓 OpDef 的 Input 未在 OpParamDef 链上声明 AutoContiguous()/IgnoreContiguous() 时，带显式 strides 的 ND 张量在 kernel launch 前被框架判为 non-contiguous，报 errno 226808025 并升级为 561000。判别：grep plog 取 226808025/561000，核查 op_host *_def.cpp 的 Input 链是否声明连续性策略；AutoContiguous 是 OpParamDef 方法而非 OpDef 方法。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [ACLNN 561102 单 dtype 原型注册与 opbuild 字节约束](../../../../runbooks/compilation/aclnn_561102_dtype_opbuild.md)（`exemplifies`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《ACLNN 561102 单 dtype 原型注册与 opbuild 字节约束》明确“多 dtype 反量化算子 ST 全失败，根因为 opbuild 要求同一算子原型内同一 input 各 dtype 字节数一致，int8/int32 不能共存于单一 REG_OP/OP_ADD，需按字节数拆分算子原型组。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [OpDef FORMAT_NCHW 致 5D 报 161002](../../../../runbooks/compilation/opdef_format_nchw_5d_161002.md)（`exemplifies`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《OpDef FORMAT_NCHW 致 5D 报 161002》明确“同时支持 4D/5D 的算子在 OpDef 注册 FORMAT_NCHW 会让 5D 张量在 GetWorkspaceSize 阶段报 ACLNN error 161002；NCHW 只对 4D 有效，该路线 banned，应保持 FORMAT_ND 并由 tiling 据 shape 推断布局。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [ValueDepend(REQUIRED) 让 axes 走 host 端](../../../../runbooks/compilation/opdef_value_depend_required_for_axes_host_read.md)（`exemplifies`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《ValueDepend(REQUIRED) 让 axes 走 host 端》明确“reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) 与 aclnnXxxTensorGetWorkspaceSize(aclTensor*) 两个 API 变体。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [optional input 未连接触发 InferShape 失败](../../../../runbooks/compilation/optional_input_infershape.md)（`exemplifies`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《optional input 未连接触发 InferShape 失败》明确“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [算子原型定义](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`explains`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《算子原型定义》明确“本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [AutoContiguous](../op_param_def/auto_contiguous.md)（`related`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《AutoContiguous》明确“配置该参数，当单算子API（aclnnxxx）接口中的输入（aclTensor类型）是非连续tensor时，框架会自动将其转换为连续tensor。 该接口仅在如下场景支持： - 通过单算子API执行的方式开发单算子调用应用。 - 间接调用单算子API\(aclnnxxx\)接口：Pytorch框架单算子直调的场景。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [Output（原型注册管理）](output.md)（`related`）：Input/Output 分别为特定处理器注册差异化原型参数，并返回 OpParamDef 继续配置；共同定义处理器专属签名。
- [Comment](../op_param_def/comment.md)（`same_topic`）：Comment 与《Input（原型注册管理）》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
- [DataTypeForBinQuery](../op_param_def/data_type_for_bin_query.md)（`same_topic`）：DataTypeForBinQuery 与《Input（原型注册管理）》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [DataType（OpParamDef）](../op_param_def/data_type.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《DataType（OpParamDef）》明确“定义算子参数数据类型。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [Follow（OpParamDef）](../op_param_def/follow.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《Follow（OpParamDef）》明确“用于指定当前输入/输出的datatype/format/shape信息与之前定义过的某个输入一致。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [Format（OpParamDef）](../op_param_def/format.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《Format（OpParamDef）》明确“定义算子参数数据格式。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [Input（OpDef）](../op_def/input.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《Input（OpDef）》明确“注册算子输入，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [OpParamDef](../op_param_def/op_param_def.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《OpParamDef》明确“OpParamDef算子参数定义接口索引。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [ParamType（OpParamDef）](../op_param_def/param_type.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《ParamType（OpParamDef）》明确“OpParamDef &ParamType(Option param_type)”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [Scalar（OpParamDef）](../op_param_def/scalar.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《Scalar（OpParamDef）》明确“配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [构造&拷贝构造函数（OpParamDef）](../op_param_def/constructor_and_copy_constructor.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《构造&拷贝构造函数（OpParamDef）》明确“构造算子参数的OpParamDef，OpParamDef用于描述算子参数的信息，如数据类型、格式等。一般用户不会直接构造OpParamDef，而是通过Input、Output接口间接构造算子参数的OpParamDef。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
<!-- cannbot:related:end -->
