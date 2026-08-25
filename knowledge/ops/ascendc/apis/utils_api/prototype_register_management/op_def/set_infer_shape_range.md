---
type: API
title: SetInferShapeRange
description: 使用图模式时，需要调用该接口注册ShapeRange推导函数。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/SetInferShapeRange.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# SetInferShapeRange

## 功能说明
使用图模式时，需要调用该接口注册ShapeRange推导函数。
## 函数原型
## 参数说明
## 返回值说明
OpDef算子定义，OpDef请参考OpDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [InferShape 返回 identity 致空 kernel 假通过](../../../../runbooks/precision/infershape_identity_kernel.md)（`exemplifies`）：SetInferShapeRange：SetInferShapeRange与SetInferShape/SetInferDataType共同构成图模式原型推导；三个 runbook分别覆盖 optional输入、原型库缺失和错误 identity 推导造成的真实失败。 目标卡《InferShape 返回 identity 致空 kernel 假通过》补充：op_host InferShape 用 *output=*input 占位时，aclnn 框架对 identity 用例走旁路 copy，空 kernel 也有用例通过，掩盖 kernel 未输出的缺陷。
- [optional input 未连接触发 InferShape 失败](../../../../runbooks/compilation/optional_input_infershape.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《SetInferShapeRange》明确提供“使用图模式时，需要调用该接口注册ShapeRange推导函数。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape](../../../../runbooks/compilation/op_proto_lib_axes_infershape.md)（`exemplifies`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《SetInferShapeRange》具体提供“使用图模式时，需要调用该接口注册ShapeRange推导函数。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [SetInferDataType](set_infer_data_type.md)（`related`）：SetInferShapeRange：SetInferShapeRange与SetInferShape/SetInferDataType共同构成图模式原型推导；三个 runbook分别覆盖 optional输入、原型库缺失和错误 identity 推导造成的真实失败。 目标卡《SetInferDataType》补充：使用图模式时，需要调用该接口注册DataType推导函数。
- [原型注册接口（OP_ADD）](../op_add.md)（`related`）：《原型注册接口（OP_ADD）》处理“注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。”。《SetInferShapeRange》明确提供“使用图模式时，需要调用该接口注册ShapeRange推导函数。”，其参数、调用或验证步骤直接接入OP_ADD 宏与 OpDef、注册函数、原型库和注册故障的可执行闭环。
- [SetInferShape](set_infer_shape.md)（`same_topic`）：SetInferShapeRange：SetInferShapeRange与SetInferShape/SetInferDataType共同构成图模式原型推导；三个 runbook分别覆盖 optional输入、原型库缺失和错误 identity 推导造成的真实失败。 目标卡《SetInferShape》补充：使用图模式时，需要调用该接口注册Shape推导函数。
<!-- cannbot:related:end -->
