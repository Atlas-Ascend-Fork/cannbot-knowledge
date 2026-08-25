---
type: API
title: ParamType（OpParamDef）
description: OpParamDef &ParamType(Option param_type)
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/ParamType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# ParamType

## 功能说明
定义算子参数类型。
## 函数原型
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [optional input 未连接触发 InferShape 失败](../../../../runbooks/compilation/optional_input_infershape.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《ParamType（OpParamDef）》明确提供“OpParamDef &ParamType(Option param_type)”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [DataType（OpParamDef）](data_type.md)（`related`）：ParamType 定义 required/optional/dynamic，需与 dtype 列表共同构成输入契约。
- [Version](version.md)（`related`）：ParamType marks an input optional; Version then assigns consecutive aclnn interface versions when such optional inputs are introduced.
- [Input（OpDef）](../op_def/input.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；ParamType（OpParamDef）正文说明“OpParamDef &ParamType(Option param_type)”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Input（原型注册管理）](../op_ai_core_config/input.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《ParamType（OpParamDef）》明确“OpParamDef &ParamType(Option param_type)”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
<!-- cannbot:related:end -->
