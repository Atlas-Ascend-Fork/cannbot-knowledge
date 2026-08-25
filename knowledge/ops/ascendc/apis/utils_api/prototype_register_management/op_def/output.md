---
type: API
title: Output（OpDef）
description: 注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/Output.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Output

## 功能说明
注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。
## 函数原型
## 参数说明
## 返回值说明
算子参数定义，OpParamDef实例，具体请参考OpParamDef。
## 约束说明
参数注册的顺序需要和算子kernel入口函数一致。

<!-- cannbot:related:start -->
## 相关

- [算子原型定义](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`explains`）：输出声明顺序会影响 aclnn 与 Kernel 参数顺序，OpDef Output 是该契约的落地接口。
- [AddOutputTd](../../tiling_tuning/context_builder/add_output_td.md)（`related`）：AddOutputTd 与《Output（OpDef）》的实质衔接是：AddOutputTd 与输入/输出/工作空间描述共同构造 tiling context；context builder、output view 故障和 OpDef Output 说明其 host 侧消费位置。
- [OpDef](op_def.md)（`related`）：“Output（OpDef）”定义：注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。；“OpDef”定义：OpDef算子定义接口索引。。实质衔接：Output 与 Input 建立 OpDef 参数契约，随后 shape/dtype 推导回调决定输出元信息；OpDef 总览给出注册链。
- [SetInferDataType](set_infer_data_type.md)（`related`）：“Output（OpDef）”定义：注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。；“SetInferDataType”定义：使用图模式时，需要调用该接口注册DataType推导函数。。实质衔接：Output 与 Input 建立 OpDef 参数契约，随后 shape/dtype 推导回调决定输出元信息；OpDef 总览给出注册链。
- [SetInferShape](set_infer_shape.md)（`related`）：“Output（OpDef）”定义：注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。；“SetInferShape”定义：使用图模式时，需要调用该接口注册Shape推导函数。。实质衔接：Output 与 Input 建立 OpDef 参数契约，随后 shape/dtype 推导回调决定输出元信息；OpDef 总览给出注册链。
- [构造&拷贝构造函数（OpParamDef）](../op_param_def/constructor_and_copy_constructor.md)（`related`）：OpDef::Output 注册输出并返回 OpParamDef，提供 focal 所述的另一合法构造路径，后续再配置输出属性。
- [Comment](../op_param_def/comment.md)（`same_topic`）：Comment 与《Output（OpDef）》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
- [EnableFallBack](enable_fall_back.md)（`same_topic`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；Output（OpDef）正文界定“注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
- [Input（OpDef）](input.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；Output（OpDef）正文说明“注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
<!-- cannbot:related:end -->
