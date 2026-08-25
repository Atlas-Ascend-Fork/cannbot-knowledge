---
type: API
title: SetInferDataType
description: 使用图模式时，需要调用该接口注册DataType推导函数。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/SetInferDataType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# SetInferDataType

## 功能说明
使用图模式时，需要调用该接口注册DataType推导函数。
## 函数原型
## 参数说明
## 返回值说明
OpDef算子定义，OpDef请参考OpDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape](../../../../runbooks/compilation/op_proto_lib_axes_infershape.md)（`exemplifies`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《SetInferDataType》具体提供“使用图模式时，需要调用该接口注册DataType推导函数。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [基本开发流程](../../../../guides/programming_guide/advanced_programming/operator_graph_development/basic_development_flow.md)（`explains`）：基本开发流程 与《SetInferDataType》的实质衔接是：算子图基本流程把 OpDef 原型、InferShape/InferDataType、图编译执行和 tiling 下沉串成同一生命周期；三个失败案例分别验证原型加载、可选输入和 shape 推导不能被绕过。
- [DataType（OpParamDef）](../op_param_def/data_type.md)（`related`）：OpParamDef 的 DataType 声明可接受类型范围，SetInferDataType 在运行 shape/输入条件下选择实际输出类型。
- [Output（OpDef）](output.md)（`related`）：“Output（OpDef）”定义：注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。；“SetInferDataType”定义：使用图模式时，需要调用该接口注册DataType推导函数。。实质衔接：Output 与 Input 建立 OpDef 参数契约，随后 shape/dtype 推导回调决定输出元信息；OpDef 总览给出注册链。
- [SetInferShape](set_infer_shape.md)（`related`）：图模式通常需要同时注册 shape 与 dtype 推导，二者共同完成输出元信息。
- [SetInferShapeRange](set_infer_shape_range.md)（`related`）：SetInferShapeRange：SetInferShapeRange与SetInferShape/SetInferDataType共同构成图模式原型推导；三个 runbook分别覆盖 optional输入、原型库缺失和错误 identity 推导造成的真实失败。 目标卡《SetInferDataType》补充：使用图模式时，需要调用该接口注册DataType推导函数。
- [DataTypeForBinQuery](../op_param_def/data_type_for_bin_query.md)（`same_topic`）：DataTypeForBinQuery 与《SetInferDataType》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [EnableFallBack](enable_fall_back.md)（`same_topic`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；SetInferDataType正文界定“使用图模式时，需要调用该接口注册DataType推导函数”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
<!-- cannbot:related:end -->
