---
type: API
title: Input（OpDef）
description: 注册算子输入，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/Input.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Input

## 功能说明
注册算子输入，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。
## 函数原型
## 参数说明
## 返回值说明
算子参数定义，OpParamDef实例，具体请参考OpParamDef。
## 约束说明
参数注册的顺序需要和算子kernel入口函数一致。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；ACLNN 561000 非连续张量需 AutoContiguous正文说明“aclnn 算子仓 OpDef 的 Input 未在 OpParamDef 链上声明 AutoContiguous()/IgnoreContiguous() 时，带显式 strides 的 ND 张量在 kernel launch 前被框架判为 non-contiguous，报 ”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [ACLNN 561102 单 dtype 原型注册与 opbuild 字节约束](../../../../runbooks/compilation/aclnn_561102_dtype_opbuild.md)（`exemplifies`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；ACLNN 561102 单 dtype 原型注册与 opbuild 字节约束正文说明“多 dtype 反量化算子 ST 全失败，根因为 opbuild 要求同一算子原型内同一 input 各 dtype 字节数一致，int8/int32 不能共存于单一 REG_OP/OP_ADD，需按字节数拆分算子原型组”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [OpDef FORMAT_NCHW 致 5D 报 161002](../../../../runbooks/compilation/opdef_format_nchw_5d_161002.md)（`exemplifies`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；OpDef FORMAT_NCHW 致 5D 报 161002正文说明“同时支持 4D/5D 的算子在 OpDef 注册 FORMAT_NCHW 会让 5D 张量在 GetWorkspaceSize 阶段报 ACLNN error 161002；NCHW 只对 4D 有效，该路线 banned，应保持 FORMAT_ND 并由 tiling 据 sh”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [ValueDepend(REQUIRED) 让 axes 走 host 端](../../../../runbooks/compilation/opdef_value_depend_required_for_axes_host_read.md)（`exemplifies`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；ValueDepend(REQUIRED) 让 axes 走 host 端正文说明“reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) ”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [optional input 未连接触发 InferShape 失败](../../../../runbooks/compilation/optional_input_infershape.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《Input（OpDef）》明确提供“注册算子输入，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [算子原型定义](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`explains`）：原型指南中的输入名称、必选性、dtype 与 format 组合由 OpDef Input 接口具体声明。
- [Comment](../op_param_def/comment.md)（`same_topic`）：Comment 与《Input（OpDef）》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
- [DataTypeForBinQuery](../op_param_def/data_type_for_bin_query.md)（`same_topic`）：DataTypeForBinQuery 与《Input（OpDef）》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [DataType（OpParamDef）](../op_param_def/data_type.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；DataType（OpParamDef）正文说明“定义算子参数数据类型”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Follow（OpParamDef）](../op_param_def/follow.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；Follow（OpParamDef）正文说明“用于指定当前输入/输出的datatype/format/shape信息与之前定义过的某个输入一致”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Format（OpParamDef）](../op_param_def/format.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；Format（OpParamDef）正文说明“定义算子参数数据格式”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Input（原型注册管理）](../op_ai_core_config/input.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《Input（OpDef）》明确“注册算子输入，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [Output（OpDef）](output.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；Output（OpDef）正文说明“注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [ParamType（OpParamDef）](../op_param_def/param_type.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；ParamType（OpParamDef）正文说明“OpParamDef &ParamType(Option param_type)”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Scalar（OpParamDef）](../op_param_def/scalar.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；Scalar（OpParamDef）正文说明“配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [原型注册接口（OP_ADD）](../op_add.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；原型注册接口（OP_ADD）正文说明“注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [构造&拷贝构造函数（OpParamDef）](../op_param_def/constructor_and_copy_constructor.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；构造&拷贝构造函数（OpParamDef）正文说明“构造算子参数的OpParamDef，OpParamDef用于描述算子参数的信息，如数据类型、格式等。一般用户不会直接构造OpParamDef，而是通过Input、Output接口间接构造算子参数的OpParamDef”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
<!-- cannbot:related:end -->
