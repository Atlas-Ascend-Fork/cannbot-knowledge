---
type: API
title: DataType（OpParamDef）
description: 定义算子参数数据类型。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/DataType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# DataType

## 功能说明
定义算子参数数据类型。
## 函数原型
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [Follow（OpParamDef）](follow.md)（`related`）：Follow 复用另一参数的 dtype/format/shape，而 DataType 显式列出允许 dtype。
- [ParamType（OpParamDef）](param_type.md)（`related`）：ParamType 定义 required/optional/dynamic，需与 dtype 列表共同构成输入契约。
- [Scalar（OpParamDef）](scalar.md)（`related`）：《DataType（OpParamDef）》明确“定义算子参数数据类型。”；它与《Scalar（OpParamDef）》的“配置该参数后，自动生成的单算子API（aclnnxxx）接口中，输入类型为aclScalar类型。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetInferDataType](../op_def/set_infer_data_type.md)（`related`）：OpParamDef 的 DataType 声明可接受类型范围，SetInferDataType 在运行 shape/输入条件下选择实际输出类型。
- [DataTypeForBinQuery](data_type_for_bin_query.md)（`same_topic`）：DataTypeForBinQuery 与《DataType（OpParamDef）》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [DataTypeList](data_type_list.md)（`same_topic`）：DataType 要求显式列出输入输出 dtype/format 组合，DataTypeList 用于某参数可与其余组合自由笛卡尔组合时去重；二者的选择决定原型组合表达。
- [Input（OpDef）](../op_def/input.md)（`same_topic`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；DataType（OpParamDef）正文说明“定义算子参数数据类型”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Input（原型注册管理）](../op_ai_core_config/input.md)（`same_topic`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《DataType（OpParamDef）》明确“定义算子参数数据类型。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [OpParamDef](op_param_def.md)（`same_topic`）：DataType 是 OpParamDef 的链式配置。
<!-- cannbot:related:end -->
